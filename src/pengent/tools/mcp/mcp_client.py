from ...lib import get_logger
from contextlib import asynccontextmanager
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from .mcp_data import ModelContextProtocolData


class ModelContextProtocolClient:
    """MCPクライアントクラス"""

    def __init__(self, mcp_data: ModelContextProtocolData):
        self.mcp_data = mcp_data
        self.session: ClientSession | None = None
        self.logger = get_logger(__name__)

    @asynccontextmanager
    async def connect(self):
        self.logger.info(
            "Connecting to MCP server: "
            f"{self.mcp_data.name} ({self.mcp_data.stream_type})"
        )
        if self.mcp_data.stream_type == "stdio":
            stream_cm = stdio_client(
                StdioServerParameters(
                    command=self.mcp_data.command,
                    args=self.mcp_data.args,
                    env=self.mcp_data.env or {},
                )
            )
            async with stream_cm as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    self.session = session
                    yield self
                    self.session = None

        elif self.mcp_data.stream_type == "streamable-http":
            stream_cm = streamablehttp_client(self.mcp_data.url)
            async with stream_cm as (read_stream, write_stream, _get_session_id):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    self.session = session
                    yield self
                    self.session = None

        else:
            raise NotImplementedError(
                f"Unsupported stream type: {self.mcp_data.stream_type}"
            )

    async def list_tools(self):
        if not self.session:
            raise RuntimeError("Session not initialized")
        ret = await self.session.list_tools()
        tools = ret.tools
        return [tool.model_dump() for tool in tools]

    async def call_tool(self, tool_name: str, params: dict):
        if not self.session:
            raise RuntimeError("Session not initialized")
        ret = await self.session.call_tool(tool_name, params)
        return ret.model_dump()

    async def ping(self) -> None:
        if not self.session:
            raise RuntimeError("Session not initialized")

        await self.session.send_ping()
        return
