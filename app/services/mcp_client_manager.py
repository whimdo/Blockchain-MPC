from __future__ import annotations

import asyncio

from app.clients.mcp_client import MCPClient, MCPQueryResult
from app.utils.logging_config import get_logger


class MCPClientManager:
    """Application-level singleton manager for the stdio MCP client."""

    def __init__(self) -> None:
        self.logger = get_logger("app.services.mcp_client_manager")
        self._client: MCPClient | None = None
        self._lifecycle_lock = asyncio.Lock()
        self._query_lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.session is not None

    async def start(self) -> None:
        async with self._lifecycle_lock:
            if self.is_connected:
                return

            client = MCPClient()
            await client.connect_to_server(client.server_path)
            self._client = client
            self.logger.info("MCP singleton client started")

    async def process_query_detailed(self, query: str) -> MCPQueryResult:
        if not self.is_connected:
            await self.start()

        if self._client is None:
            raise RuntimeError("MCP singleton client is not available")

        # The MCP stdio session is stateful, so keep requests serialized.
        async with self._query_lock:
            try:
                return await self._client.process_query_detailed(query)
            except Exception:
                self.logger.exception("MCP singleton query failed")
                raise

    async def cleanup(self) -> None:
        async with self._lifecycle_lock:
            if self._client is None:
                return

            try:
                await self._client.cleanup()
                self.logger.info("MCP singleton client cleaned up")
            finally:
                self._client = None


mcp_client_manager = MCPClientManager()
