from typing import Any
import csv
from mcp.server.fastmcp import FastMCP
from datetime import datetime

mcp = FastMCP("demo")

# Constants
DATA_CSV = "E:\\-bishe\\Blockchain-MPC\\MCP\\server\\output.csv"


@mcp.tool()
def find_url_by_doc_id(doc_id: str) -> str:
    """根据 doc_id 在 CSV 中查找并返回对应 URL。"""
    with open(DATA_CSV, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            # 确保行包含足够列，并用第 7 列匹配 doc_id，第 9 列返回 URL
            if len(row) > 8 and row[6].strip() == doc_id:
                return row[8].strip()
    return f"i can`t find the url with {doc_id}"


if __name__ == "__main__":
    # 启动 MCP Server
    mcp.run(transport="stdio")
