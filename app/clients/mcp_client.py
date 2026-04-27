from __future__ import annotations

import asyncio
import json
import os
import sys
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

from app.utils.logging_config import get_logger
from configs.ai_config import load_ai_config
from configs.mcp_config import load_mcp_config


@dataclass
class MCPToolCallLog:
    tool_call_id: str | None
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    status: str = "success"
    duration_ms: int | None = None
    result_text: str | None = None
    parsed_result: Any = None
    error_message: str | None = None


@dataclass
class MCPQueryResult:
    answer: str
    tool_calls: list[MCPToolCallLog] = field(default_factory=list)
    messages: list[dict[str, Any]] = field(default_factory=list)


class MCPClient:
    """MCP stdio client with OpenAI-compatible tool calling."""

    def __init__(self) -> None:
        self.logger = get_logger("app.clients.mcp_client")
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()

        self.ai_config = load_ai_config()
        self.mcp_config = load_mcp_config()
        self.server_path = self.mcp_config.server_script_path
        if not self.ai_config.api_key:
            raise RuntimeError("Missing AI_API_KEY")

        self.ai_client = OpenAI(
            base_url=self.ai_config.base_url,
            api_key=self.ai_config.api_key,
            max_retries=0,
        )

    async def connect_to_server(self, server_script_path: str) -> None:
        """Connect to a Python or Node MCP server through stdio."""
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = sys.executable if is_python else "node"
        child_env = os.environ.copy()
        project_root = str(Path(__file__).resolve().parents[2])
        existing_pythonpath = child_env.get("PYTHONPATH")
        child_env["PYTHONPATH"] = (
            project_root
            if not existing_pythonpath
            else f"{project_root}{os.pathsep}{existing_pythonpath}"
        )

        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=child_env,
        )

        self.logger.info("Connecting to MCP server command=%s script=%s", command, server_script_path)
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))
        await self.session.initialize()

        tools_response = await self.session.list_tools()
        prompts_response = await self.session.list_prompts()
        resource_templates_response = await self.session.list_resource_templates()

        self.logger.info(
            "Connected to MCP server tools=%s prompts=%s resource_templates=%s",
            [tool.name for tool in tools_response.tools],
            [prompt.name for prompt in prompts_response.prompts],
            [resource.name for resource in resource_templates_response.resourceTemplates],
        )

    async def process_query(self, query: str) -> str:
        """Let the model choose MCP tools, execute them, then return the final answer."""
        result = await self.process_query_detailed(query)
        return result.answer

    async def process_query_detailed(self, query: str) -> MCPQueryResult:
        """Let the model choose MCP tools and return the final answer plus tool call logs."""
        if self.session is None:
            raise RuntimeError("MCP server is not connected")

        messages: list[dict[str, Any]] = [{"role": "user", "content": query}]
        tool_call_logs: list[MCPToolCallLog] = []
        self.logger.info("MCP query started query=%s", query)
        self.logger.debug("Initial messages=%s", serialize_messages(messages))

        available_tools = await self.list_openai_tools()
        self.logger.info("MCP available tools count=%s", len(available_tools))
        self.logger.debug("MCP available tools=%s", json.dumps(available_tools, ensure_ascii=False))

        first_request: dict[str, Any] = {
            "model": self.ai_config.model,
            "messages": messages,
            "max_tokens": 8192,
            "temperature": 0,
            "timeout": self.ai_config.timeout_seconds,
        }
        if available_tools:
            first_request["tools"] = available_tools
            first_request["tool_choice"] = "auto"

        first_response = await self._create_completion(first_request)
        self.logger.info("first response = %s", serialize_messages(first_response))

        first_message = first_response.choices[0].message
        tool_calls = list(first_message.tool_calls or [])
        messages.append(
            {
                "role": "assistant",
                "content": first_message.content,
                "tool_calls": [self._tool_call_to_dict(tool_call) for tool_call in tool_calls],
            }
        )
        self.logger.info("Messages after first AI response=%s", serialize_messages(messages))

        if tool_calls:
            for tool_call in tool_calls:
                arguments = self._parse_tool_arguments(tool_call.function.arguments)
                self.logger.info(
                    "Calling MCP tool name=%s arguments=%s",
                    tool_call.function.name,
                    json.dumps(arguments, ensure_ascii=False),
                )
                started = perf_counter()
                try:
                    tool_result = await self.session.call_tool(tool_call.function.name, arguments=arguments)
                    duration_ms = int((perf_counter() - started) * 1000)
                    tool_text = self._tool_result_to_text(tool_result)
                    tool_call_logs.append(
                        MCPToolCallLog(
                            tool_call_id=tool_call.id,
                            tool_name=tool_call.function.name,
                            arguments=arguments,
                            status="success",
                            duration_ms=duration_ms,
                            result_text=tool_text,
                            parsed_result=self._parse_tool_result_text(tool_text),
                        )
                    )
                except Exception as exc:
                    duration_ms = int((perf_counter() - started) * 1000)
                    tool_text = json.dumps({"ok": False, "message": str(exc)}, ensure_ascii=False)
                    tool_call_logs.append(
                        MCPToolCallLog(
                            tool_call_id=tool_call.id,
                            tool_name=tool_call.function.name,
                            arguments=arguments,
                            status="failed",
                            duration_ms=duration_ms,
                            result_text=tool_text,
                            error_message=str(exc),
                        )
                    )
                    self.logger.exception("MCP tool call failed name=%s", tool_call.function.name)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": tool_text,
                    }
                )
                self.logger.info("MCP tool call finished name=%s", tool_call.function.name)
                self.logger.info("MCP tool result name=%s result=%s", tool_call.function.name, tool_text)

            final_response = await self._create_completion(
                {
                    "model": self.ai_config.model,
                    "messages": messages,
                    "max_tokens": 8192,
                    "temperature": 0,
                    "timeout": self.ai_config.timeout_seconds,
                }
            )
        else:
            final_response = first_response

        final_content = final_response.choices[0].message.content or ""
        messages.append({"role": "assistant", "content": final_content})
        self.logger.debug("Final MCP messages=%s", serialize_messages(messages))
        self.logger.info("MCP query completed")
        return MCPQueryResult(answer=final_content.strip(), tool_calls=tool_call_logs, messages=messages)

    async def list_openai_tools(self) -> list[dict[str, Any]]:
        """Convert MCP tool schemas into OpenAI-compatible tool definitions."""
        if self.session is None:
            raise RuntimeError("MCP server is not connected")

        response = await self.session.list_tools()
        tools: list[dict[str, Any]] = []
        for tool in response.tools:
            input_schema = dict(tool.inputSchema or {})
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": {
                            "type": input_schema.get("type", "object"),
                            "properties": input_schema.get("properties", {}),
                            "required": input_schema.get("required", []),
                        },
                    },
                }
            )
        return tools

    async def chat_loop(self) -> None:
        """Run an interactive CLI loop. Intended for local debugging only."""
        self.logger.info("MCP client started. Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() == "quit":
                    break

                response = await self.process_query(query)
                self.logger.info("MCP response=%s", response)
            except Exception:
                self.logger.exception("MCP chat loop error")

    async def cleanup(self) -> None:
        """Clean up MCP stdio resources."""
        await self.exit_stack.aclose()
        self.session = None
        self.logger.info("MCP client cleanup completed")

    async def _create_completion(self, request: dict[str, Any]) -> Any:
        return await asyncio.to_thread(self.ai_client.chat.completions.create, **request)

    @staticmethod
    def _parse_tool_arguments(arguments: Any) -> dict[str, Any]:
        if arguments is None:
            return {}
        if isinstance(arguments, dict):
            return arguments
        if isinstance(arguments, str):
            try:
                parsed = json.loads(arguments)
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}

    @staticmethod
    def _tool_call_to_dict(tool_call: Any) -> dict[str, Any]:
        return {
            "id": tool_call.id,
            "type": "function",
            "function": {
                "name": tool_call.function.name,
                "arguments": tool_call.function.arguments,
            },
        }

    @staticmethod
    def _tool_result_to_text(tool_result: Any) -> str:
        content = getattr(tool_result, "content", None) or []
        parts: list[str] = []
        for item in content:
            text = getattr(item, "text", None)
            if text is not None:
                parts.append(str(text))
            else:
                parts.append(str(item))
        return "\n".join(parts)

    @staticmethod
    def _parse_tool_result_text(text: str | None) -> Any:
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text


def serialize_messages(messages: Any) -> str:
    """Serialize OpenAI/MCP message objects for debug logs."""

    def serialize(obj: Any) -> Any:
        if isinstance(obj, list):
            return [serialize(item) for item in obj]
        if isinstance(obj, dict):
            return {key: serialize(value) for key, value in obj.items()}
        if hasattr(obj, "model_dump"):
            return serialize(obj.model_dump())
        if hasattr(obj, "__dict__"):
            return {key: serialize(value) for key, value in obj.__dict__.items()}
        return obj

    return json.dumps(serialize(messages), indent=2, ensure_ascii=False)


async def main() -> None:
    client = MCPClient()
    try:
        await client.connect_to_server(client.server_path)
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
