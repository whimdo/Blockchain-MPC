import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class MCPConfig:
    server_script_path: str


def load_mcp_config() -> MCPConfig:
    """Load MCP server config from environment variables."""
    return MCPConfig(
        server_script_path=os.getenv(
            "MCP_SERVER_SCRIPT_PATH",
            "./app/services/mcp_service.py",
        ),
    )
