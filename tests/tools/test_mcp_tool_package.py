import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pengent.tools.mcp.mcp_tool_package import McpToolPackage, McpTool
from pengent.tools.mcp.mcp_client import ModelContextProtocolClient


class TestMcpTool:
    """McpToolクラスのテストクラス"""

    def test_init(self):
        """McpToolの初期化テスト"""
        # Arrange
        mock_client = MagicMock(spec=ModelContextProtocolClient)
        meta_data = {
            "name": "test_tool",
            "description": "A test tool",
            "inputSchema": {
                "type": "object",
                "properties": {"param1": {"type": "string"}},
            },
        }

        # Act
        tool = McpTool(mock_client, meta_data)

        # Assert
        assert tool.client == mock_client
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool._meta_data == meta_data

    def test_strip_schema_noise_removes_title(self):
        """_strip_schema_noiseがtitleキーを削除することのテスト"""
        # Arrange
        schema = {
            "type": "object",
            "title": "Should be removed",
            "properties": {"field1": {"type": "string", "title": "Also removed"}},
        }

        # Act
        result = McpTool._strip_schema_noise(schema)

        # Assert
        assert "title" not in result
        assert "title" not in result["properties"]["field1"]
        assert result["type"] == "object"
        assert result["properties"]["field1"]["type"] == "string"

    def test_strip_schema_noise_handles_list(self):
        """_strip_schema_noiseがリストを処理できることのテスト"""
        # Arrange
        schema = [{"type": "string", "title": "Remove"}, {"type": "number"}]

        # Act
        result = McpTool._strip_schema_noise(schema)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert "title" not in result[0]
        assert result[0]["type"] == "string"

    def test_parameters_schema_with_input_schema(self):
        """parameters_schemaメソッドのテスト(inputSchemaあり)"""
        # Arrange
        mock_client = MagicMock(spec=ModelContextProtocolClient)
        meta_data = {
            "name": "test_tool",
            "inputSchema": {
                "type": "object",
                "title": "Should be removed",
                "properties": {"param1": {"type": "string"}},
            },
        }
        tool = McpTool(mock_client, meta_data)

        # Act
        result = tool.parameters_schema()

        # Assert
        assert "title" not in result
        assert result["type"] == "object"
        assert "param1" in result["properties"]

    def test_parameters_schema_without_input_schema(self):
        """parameters_schemaメソッドのテスト(inputSchemaなし)"""
        # Arrange
        mock_client = MagicMock(spec=ModelContextProtocolClient)
        meta_data = {"name": "test_tool"}
        tool = McpTool(mock_client, meta_data)

        # Act
        result = tool.parameters_schema()

        # Assert
        assert result == {}

    @patch("asyncio.run")
    def test_run_calls_async_run(self, mock_asyncio_run):
        """runメソッドが_runを呼び出すことのテスト"""
        # Arrange
        mock_client = MagicMock(spec=ModelContextProtocolClient)
        meta_data = {"name": "test_tool"}
        tool = McpTool(mock_client, meta_data)
        mock_asyncio_run.return_value = "result"

        # Act
        result = tool.run(param1="value1", param2="value2")

        # Assert
        mock_asyncio_run.assert_called_once()
        assert result == "result"

    @pytest.mark.asyncio
    async def test_async_run_success(self):
        """_runメソッドの成功ケーステスト"""
        # Arrange
        mock_client = MagicMock(spec=ModelContextProtocolClient)
        mock_client.connect = MagicMock()
        mock_client.connect.return_value.__aenter__ = AsyncMock()
        mock_client.connect.return_value.__aexit__ = AsyncMock()
        mock_client.call_tool = AsyncMock(return_value="tool_result")

        meta_data = {"name": "test_tool"}
        tool = McpTool(mock_client, meta_data)
        params = {"param1": "value1"}

        # Act
        result = await tool._run(params)

        # Assert
        mock_client.call_tool.assert_called_once_with("test_tool", params)
        assert result == "tool_result"

    @pytest.mark.asyncio
    async def test_async_run_error(self):
        """_runメソッドのエラーケーステスト"""
        # Arrange
        mock_client = MagicMock(spec=ModelContextProtocolClient)
        mock_client.mcp_data = MagicMock()
        mock_client.mcp_data.name = "test_mcp"
        mock_client.connect = MagicMock()
        mock_client.connect.return_value.__aenter__ = AsyncMock()
        mock_client.connect.return_value.__aexit__ = AsyncMock()
        mock_client.call_tool = AsyncMock(side_effect=Exception("Connection error"))

        meta_data = {"name": "test_tool"}
        tool = McpTool(mock_client, meta_data)
        params = {"param1": "value1"}

        # Act
        result = await tool._run(params)

        # Assert
        assert "Failed to call tool 'test_tool'" in result
        assert "Connection error" in result


class TestMcpToolPackage:
    """McpToolPackageクラスのテストクラス"""

    def test_init_with_stdio_no_sync(self):
        """stdio形式でインスタンス化のテスト(sync_connect=False)"""
        # Arrange
        name = "test_package"
        command = "python"
        args = ["-m", "module"]

        # Act
        package = McpToolPackage(
            name=name,
            stream_type="stdio",
            command=command,
            args=args,
            sync_connect=False,
        )

        # Assert
        assert package.tools == []
        assert package.mcp_data.name == name
        assert package.mcp_data.stream_type == "stdio"
        assert package.mcp_data.command == command
        assert package.mcp_data.args == args
        assert isinstance(package.client, ModelContextProtocolClient)

    def test_init_with_http_no_sync(self):
        """HTTP形式でインスタンス化のテスト(sync_connect=False)"""
        # Arrange
        name = "test_http_package"
        url = "https://example.com/mcp"
        allowed_methods = ["GET", "POST"]
        headers = {"Authorization": "Bearer token"}

        # Act
        package = McpToolPackage(
            name=name,
            stream_type="streamable-http",
            url=url,
            allowed_methods=allowed_methods,
            headers=headers,
            sync_connect=False,
        )

        # Assert
        assert package.mcp_data.name == name
        assert package.mcp_data.stream_type == "streamable-http"
        assert package.mcp_data.url == url
        assert package.mcp_data.allowed_methods == allowed_methods
        assert package.mcp_data.headers == headers

    def test_init_with_env(self):
        """環境変数付きでインスタンス化のテスト"""
        # Arrange
        env = {"NODE_ENV": "production", "API_KEY": "secret"}

        # Act
        package = McpToolPackage(
            name="test_package",
            stream_type="stdio",
            command="node",
            args=["server.js"],
            env=env,
            sync_connect=False,
        )

        # Assert
        assert package.mcp_data.env == env

    def test_create_mcp_stdio(self):
        """create_mcp_stdioクラスメソッドのテスト"""
        # Arrange
        name = "stdio_package"
        command = "python"
        args = ["-m", "test"]
        env = {"PATH": "/usr/bin"}

        # Act
        with patch.object(McpToolPackage, "connect_sync"):
            package = McpToolPackage.create_mcp_stdio(
                name=name, command=command, args=args, env=env
            )

        # Assert
        assert package.mcp_data.name == name
        assert package.mcp_data.stream_type == "stdio"
        assert package.mcp_data.command == command
        assert package.mcp_data.args == args
        assert package.mcp_data.env == env

    def test_create_mcp_stdio_without_env(self):
        """create_mcp_stdioクラスメソッドのテスト(envなし)"""
        # Arrange
        name = "stdio_package"
        command = "bash"
        args = ["script.sh"]

        # Act
        with patch.object(McpToolPackage, "connect_sync"):
            package = McpToolPackage.create_mcp_stdio(
                name=name, command=command, args=args
            )

        # Assert
        assert package.mcp_data.env is None

    def test_create_mcp_http_stream(self):
        """create_mcp_http_streamクラスメソッドのテスト"""
        # Arrange
        name = "http_package"
        url = "https://api.example.com"
        allowed_methods = ["GET", "POST"]
        headers = {"Content-Type": "application/json"}

        # Act
        with patch.object(McpToolPackage, "connect_sync"):
            package = McpToolPackage.create_mcp_http_stream(
                name=name, url=url, allowed_methods=allowed_methods, headers=headers
            )

        # Assert
        assert package.mcp_data.name == name
        assert package.mcp_data.stream_type == "streamable-http"
        assert package.mcp_data.url == url
        assert package.mcp_data.allowed_methods == allowed_methods
        assert package.mcp_data.headers == headers

    def test_get_tools_empty(self):
        """get_toolsメソッドのテスト(ツールなし)"""
        # Arrange
        package = McpToolPackage(
            name="test",
            stream_type="stdio",
            command="python",
            args=[],
            sync_connect=False,
        )

        # Act
        result = package.get_tools()

        # Assert
        assert result == []

    def test_get_tools_with_tools(self):
        """get_toolsメソッドのテスト(ツールあり)"""
        # Arrange
        package = McpToolPackage(
            name="test",
            stream_type="stdio",
            command="python",
            args=[],
            sync_connect=False,
        )
        tools = [
            {"name": "tool1", "description": "Tool 1"},
            {"name": "tool2", "description": "Tool 2"},
        ]
        package.mcp_data.tools = tools

        # Act
        result = package.get_tools()

        # Assert
        assert result == tools
        assert len(result) == 2

    @patch("asyncio.run")
    def test_call_tool_success(self, mock_asyncio_run):
        """call_toolメソッドの成功ケーステスト"""
        # Arrange
        package = McpToolPackage(
            name="test",
            stream_type="stdio",
            command="python",
            args=[],
            sync_connect=False,
        )
        package.mcp_data.status = "active"
        mock_asyncio_run.return_value = "tool_result"

        # Act
        result = package.call_tool("test_tool", {"param": "value"})

        # Assert
        mock_asyncio_run.assert_called_once()
        assert result == "tool_result"

    def test_call_tool_not_connected(self):
        """call_toolメソッドのテスト(未接続)"""
        # Arrange
        package = McpToolPackage(
            name="test",
            stream_type="stdio",
            command="python",
            args=[],
            sync_connect=False,
        )
        package.mcp_data.status = "disconnected"

        # Act
        result = package.call_tool("test_tool", {"param": "value"})

        # Assert
        assert "Failed to call tool on MCP server" in result
        assert "not connected" in result

    @pytest.mark.asyncio
    async def test_async_call_tool_success(self):
        """_call_toolメソッドの成功ケーステスト"""
        # Arrange
        package = McpToolPackage(
            name="test",
            stream_type="stdio",
            command="python",
            args=[],
            sync_connect=False,
        )
        package.client.connect = MagicMock()
        package.client.connect.return_value.__aenter__ = AsyncMock()
        package.client.connect.return_value.__aexit__ = AsyncMock()
        package.client.call_tool = AsyncMock(return_value="tool_result")

        # Act
        result = await package._call_tool("test_tool", {"param": "value"})

        # Assert
        package.client.call_tool.assert_called_once_with(
            "test_tool", {"param": "value"}
        )
        assert result == "tool_result"

    @pytest.mark.asyncio
    async def test_async_call_tool_error(self):
        """_call_toolメソッドのエラーケーステスト"""
        # Arrange
        package = McpToolPackage(
            name="test",
            stream_type="stdio",
            command="python",
            args=[],
            sync_connect=False,
        )
        package.client.connect = MagicMock()
        package.client.connect.return_value.__aenter__ = AsyncMock()
        package.client.connect.return_value.__aexit__ = AsyncMock()
        package.client.call_tool = AsyncMock(side_effect=Exception("Tool error"))

        # Act
        result = await package._call_tool("test_tool", {"param": "value"})

        # Assert
        assert "Failed to call tool 'test_tool'" in result
        assert "Tool error" in result

    @pytest.mark.asyncio
    async def test_async_connect_success(self):
        """_connectメソッドの成功ケーステスト"""
        # Arrange
        package = McpToolPackage(
            name="test",
            stream_type="stdio",
            command="python",
            args=[],
            sync_connect=False,
        )

        mock_tools = [
            {"name": "tool1", "description": "Tool 1", "inputSchema": {}},
            {"name": "tool2", "description": "Tool 2", "inputSchema": {}},
        ]

        package.client.connect = MagicMock()
        package.client.connect.return_value.__aenter__ = AsyncMock()
        package.client.connect.return_value.__aexit__ = AsyncMock()
        package.client.ping = AsyncMock()
        package.client.list_tools = AsyncMock(return_value=mock_tools)

        # Act
        await package._connect()

        # Assert
        package.client.ping.assert_called_once()
        package.client.list_tools.assert_called_once()
        assert package.mcp_data.tools == mock_tools
        assert package.mcp_data.status == "active"
        assert len(package.tools) == 2
        assert all(isinstance(tool, McpTool) for tool in package.tools)

    @pytest.mark.asyncio
    async def test_async_connect_error(self):
        """_connectメソッドのエラーケーステスト"""
        # Arrange
        package = McpToolPackage(
            name="test",
            stream_type="stdio",
            command="python",
            args=[],
            sync_connect=False,
        )

        package.client.connect = MagicMock()
        package.client.connect.return_value.__aenter__ = AsyncMock()
        package.client.connect.return_value.__aexit__ = AsyncMock()
        package.client.ping = AsyncMock(side_effect=Exception("Connection failed"))

        # Act
        await package._connect()

        # Assert
        assert package.mcp_data.status == "disconnected"

    @patch("asyncio.run")
    def test_connect_sync(self, mock_asyncio_run):
        """connect_syncメソッドのテスト"""
        # Arrange
        package = McpToolPackage(
            name="test",
            stream_type="stdio",
            command="python",
            args=[],
            sync_connect=False,
        )

        # Act
        package.connect_sync()

        # Assert
        mock_asyncio_run.assert_called_once()

    def test_all_optional_parameters(self):
        """全てのオプショナルパラメータのテスト"""
        # Arrange & Act
        package = McpToolPackage(
            name="complex_package",
            stream_type="stdio",
            command="python",
            args=["-m", "module", "--option"],
            url="https://example.com",
            allowed_methods=["GET"],
            headers={"Auth": "token"},
            env={"KEY": "value"},
            sync_connect=False,
        )

        # Assert
        assert package.mcp_data.command == "python"
        assert len(package.mcp_data.args) == 3
        assert package.mcp_data.url == "https://example.com"
        assert package.mcp_data.allowed_methods == ["GET"]
        assert package.mcp_data.headers == {"Auth": "token"}
        assert package.mcp_data.env == {"KEY": "value"}
