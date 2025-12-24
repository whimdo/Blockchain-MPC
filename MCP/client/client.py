from openai import OpenAI
import asyncio
import json
import os


from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from dotenv import load_dotenv


load_dotenv()
llm_client = OpenAI(
    base_url=os.getenv("API_URL"),
    # api_key=os.getenv("OPENAI_API_KEY"),
    api_key = "sk-eDpJUi9nRVwbyuFQfTr7VARN4eMx53uASSseQaIP9k28XzCY",    
)


class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def process_query(self, query: str) -> str:
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        print("初始化 messages:")
        print(json.dumps(messages, indent=4, ensure_ascii=False))

        # 获取可用工具
        response = await self.session.list_tools()
        available_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": tool.inputSchema["type"],
                    "required": tool.inputSchema["required"],
                    "properties": tool.inputSchema["properties"],
                }
            }
        } for tool in response.tools]

        print("可用工具:")
        print(json.dumps(available_tools, indent=4, ensure_ascii=False))

        # 发送第一次 LLM 请求
        first_response = llm_client.chat.completions.create(
            model=os.getenv("MODEL_NAME"),
            messages=messages,
            tools=available_tools,
            tool_choice="required",
            max_tokens=100,
            temperature=0,
            timeout=120
        )

        print("第一次 LLM 响应:")
        print(first_response)

        # 记录 LLM 的初步响应
        messages.append(
            {
                "role": "assistant",
                "content": first_response.choices[0].message.content,
                "tool_calls": first_response.choices[0].message.tool_calls,
            }
        )

        print("LLM 初步响应后 messages:")
        print(messages)

        stop_reason = (
            "tool_calls"
            if first_response.choices[0].message.tool_calls is not None
            else first_response.choices[0].finish_reason
        )

        if stop_reason == "tool_calls":
            # 处理工具调用
            for tool_call in first_response.choices[0].message.tool_calls:
                arguments = (
                    json.loads(tool_call.function.arguments)
                    if isinstance(tool_call.function.arguments, str)
                    else tool_call.function.arguments
                )
                tool_result = await self.session.call_tool(tool_call.function.name, arguments=arguments)

                # 记录工具调用结果
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": tool_result.content[0].text,
                    }
                )
                messages1=[
                    {
                        "role": "user",
                        "content": f"answer of the question might be{tool_result.content[0].text}"
                    }
                ]

            print("工具调用后 messages:")
            print(messages)

            # 让 LLM 结合工具结果再思考一次
            new_response = llm_client.chat.completions.create(
                model=os.getenv("MODEL_NAME"),
                messages=messages1,
                max_tokens=200,
            )

        elif stop_reason == "stop":
            new_response = first_response
        else:
            raise ValueError(f"Unknown stop reason: {stop_reason}")

        # 记录最终 LLM 响应
        messages.append(
            {"role": "assistant", "content": new_response.choices[0].message.content}
        )

        print("最终 LLM 响应后 messages:")
        print(messages)

        return new_response.choices[0].message.content


    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


    async def connect_to_server(self, server_script_path: str):
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        tools_response = await self.session.list_tools()
        tools = tools_response.tools
        # print("Connected to server with tools:", [tool for tool in tools])

        prompts_response = await self.session.list_prompts()
        prompts = prompts_response.prompts
        # print("Connected to server with prompts:", [prompt for prompt in prompts])

        resources_templates_response = await self.session.list_resource_templates()
        resources = resources_templates_response.resourceTemplates
        # print("Connected to server with resources:", [resource for resource in resources])

def serialize_messages(messages):
    """ 处理 messages，确保所有对象都可序列化 """
    def serialize(obj):
        if isinstance(obj, list):
            return [serialize(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return {key: serialize(value) for key, value in obj.__dict__.items()}
        else:
            return obj  # 其他数据类型，直接返回

    return json.dumps(serialize(messages), indent=4, ensure_ascii=False)

async def main():
    client = MCPClient()
    try:
        await client.connect_to_server("../server/server.py")
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())