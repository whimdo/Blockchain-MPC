from typing import Any
import csv
from mcp.server.fastmcp import FastMCP
from datetime import datetime

mcp = FastMCP("demo")

# Constants
DATA_CSV="E:\-bishe\Blockchain-MPC\MCP\server\output.csv"

@mcp.tool()
def find_url_by_doc_id(doc_id: str) -> str:
    """
Find the corresponding URL in the CSV file based on the doc_id.
input:doc_id (str): The doc_id to query 
Returns:str:The matching URL.
"""
    with open(DATA_CSV, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            # 确保行有足够的列，且第七列索引为 6，第九列索引为 8
            if len(row) > 8 and row[6].strip() == doc_id:
                return row[8].strip()  # 返回第九列并去除首尾空格
    return f"i can`t find the url with {doc_id}"

if __name__ == "__main__":
    # 启动server
    mcp.run(transport='stdio')