import sys
import os
import asyncio

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "src")
    )
)

from pengent.tools.mcp.mcp_client import (
    ModelContextProtocolClient,
    ModelContextProtocolData,
)


async def mpc_stdio_client_example():
    # Create ModelContextProtocolData for MCP server
    data = ModelContextProtocolData.create_mcp_stdio(
        name="example_stdio_mcp",
        command="python",
        args=["example/tool/mcp/server.py"],
    )

    client = ModelContextProtocolClient(data)
    async with client.connect():
        await client.ping()

        # List available tools
        tools = await client.list_tools()
        print("Available tools:", tools)

        print("")

        # Call a tool
        result = await client.call_tool("hello_world", {"name": "World"})
        print("Tool call result:", result)


async def mpc_http_client_example():
    # Create ModelContextProtocolData for MCP server
    data = ModelContextProtocolData.create_mcp_http_stream(
        url="http://localhost:8000/mcp",
        allowed_methods=["hello_world"],
        headers={"Authorization": "Bearer YOUR_API_KEY"},
    )

    client = ModelContextProtocolClient(data)
    async with client.connect():
        await client.ping()

        # List available tools
        tools = await client.list_tools()
        print("Available tools:", tools)

        print("")

        # Call a tool
        result = await client.call_tool("hello_world", {"name": "World"})
        print("Tool call result:", result)


asyncio.run(mpc_stdio_client_example())
# asyncio.run(mpc_http_client_example())
