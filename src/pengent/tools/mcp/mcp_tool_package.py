import asyncio
from typing import Any, Optional
from .mcp_data import ModelContextProtocolData
from .mcp_client import ModelContextProtocolClient
from ...type.tool.tool_enum import (
    ToolBase,
)


class McpTool(ToolBase):
    """
    MCPツールを実行するためのクラス
    """

    def __init__(
        self,
        client: ModelContextProtocolClient,
        meta_data: Optional[dict[str, Any]],
    ):
        self.client = client
        self.name = meta_data.get("name")
        self.description = meta_data.get("description")
        self._meta_data = meta_data

    @classmethod
    def _strip_schema_noise(cls, schema: dict) -> dict:
        """
        JSON Schema から title キーを再帰的に削除する
        """
        if isinstance(schema, dict):
            return {
                k: cls._strip_schema_noise(v) for k, v in schema.items() if k != "title"
            }
        if isinstance(schema, list):
            return [cls._strip_schema_noise(x) for x in schema]
        return schema

    def parameters_schema(self) -> dict:
        input_schema = self._meta_data.get("inputSchema")
        if not input_schema:
            return {}

        return self._strip_schema_noise(input_schema)

    def run(self, **kwargs) -> Any:
        # MCPサーバー上のツールを呼び出す
        return asyncio.run(self._run(kwargs))

    async def _run(self, params: dict):
        """非同期的にMCPサーバーに接続するメソッド"""
        async with self.client.connect():
            try:
                result = await self.client.call_tool(self.name, params)
                return result
            except Exception as e:
                error_msg = f"Failed to call tool '{self.name}' on MCP"
                error_msg += f" {self.client.mcp_data.name}, Error: {e}"
                return error_msg


class McpToolPackage:
    """MCP用のツールパッケージクラス"""

    def __init__(
        self,
        name: str,
        stream_type: str,
        args: Optional[list[str]] = None,
        url: Optional[str] = None,
        allowed_methods: Optional[list[str]] = None,
        headers: Optional[dict[str, str]] = None,
        command: Optional[str] = None,
        env: Optional[dict[str, str]] = None,
        sync_connect: bool = True,
    ):
        """MCP用のツールパッケージクラスのコンストラクタ"""
        print("Initialized McpToolPackage")
        # 内部用のMCPツールリスト
        self.tools: list[McpTool] = []
        self.mcp_data = ModelContextProtocolData(
            name=name,
            stream_type=stream_type,
            args=args,
            url=url,
            allowed_methods=allowed_methods,
            headers=headers,
            command=command,
            env=env,
        )
        self.client = ModelContextProtocolClient(self.mcp_data)
        if sync_connect:
            self.connect_sync()

    def connect_sync(self) -> Any:
        """同期的にMCPサーバーに接続するメソッド"""
        asyncio.run(self._connect())

    async def _connect(self) -> Any:
        """非同期的にMCPサーバーに接続するメソッド"""
        async with self.client.connect():
            try:
                await self.client.ping()
                tools = await self.client.list_tools()
                self.mcp_data.tools = tools
                self.mcp_data.status = "active"
                for tool_meta in tools:
                    mcp_tool = McpTool(self.client, tool_meta)
                    self.tools.append(mcp_tool)
            except Exception as e:
                print(f"Failed to connect to MCP: {self.mcp_data}, Error: {e}")
                self.mcp_data.status = "disconnected"

    def get_tools(self) -> list:
        """MCPサーバーから取得したツールリストを返すメソッド"""
        return self.mcp_data.tools or []

    def call_tool(self, tool_name: str, params: dict) -> str:
        """同期的にMCPサーバーに接続するメソッド"""
        try:
            if self.mcp_data.status != "active":
                raise RuntimeError("MCP server is not connected.")

            return asyncio.run(self._call_tool(tool_name, params))
        except Exception as e:
            print(f"Failed to call tool on MCP: {self.mcp_data.name}")
            print(f"Error: {e}")
            return f"Failed to call tool on MCP server: {e}"

    async def _call_tool(self, tool_name: str, params: dict):
        """非同期的にMCPサーバーに接続するメソッド"""
        async with self.client.connect():
            try:
                result = await self.client.call_tool(tool_name, params)
                return result
            except Exception as e:
                error_msg = f"Failed to call tool '{tool_name}' on MCP"
                error_msg += f" {self.mcp_data.name}, Error: {e}"
                return error_msg

    @classmethod
    def create_mcp_stdio(
        cls,
        name: str,
        command: str,
        args: list[str],
        env: Optional[dict[str, str]] = None,
    ) -> "McpToolPackage":
        return cls(name=name, stream_type="stdio", command=command, args=args, env=env)

    @classmethod
    def create_mcp_http_stream(
        cls,
        name: str,
        url: str,
        allowed_methods: Optional[list[str]] = None,
        headers: Optional[dict[str, str]] = None,
        env: Optional[dict[str, str]] = None,
    ) -> "McpToolPackage":
        return cls(
            name=name,
            stream_type="streamable-http",
            url=url,
            allowed_methods=allowed_methods,
            headers=headers,
            env=env,
        )
