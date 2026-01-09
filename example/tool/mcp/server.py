from mcp.server.fastmcp import FastMCP

# "hello" という名前のサーバを作成
mcp = FastMCP("hello")

# MCPツールとしてhello_world関数を登録
@mcp.tool()
async def hello_world(name: str) -> str:
    return f"Hello, {name}!"

if __name__ == "__main__":
    # 標準入出力で通信(stdio使用)
    mcp.run(transport="stdio")
