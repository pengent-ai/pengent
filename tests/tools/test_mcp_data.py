import pytest
from pengent.tools.mcp.mcp_data import ModelContextProtocolData


class TestModelContextProtocolData:
    """ModelContextProtocolDataクラスのテストクラス"""

    def test_create_mcp_stdio_success(self):
        """stdio形式のMCPデータ作成のテスト"""
        # Arrange
        command = "python"
        args = ["--version"]

        # Act
        mcp_data = ModelContextProtocolData.create_mcp_stdio(
            name="test_mcp", command=command, args=args
        )

        # Assert
        assert mcp_data.stream_type == "stdio"
        assert mcp_data.command == command
        assert mcp_data.args == args
        assert mcp_data.status == "initializing"
        assert mcp_data.url is None
        assert mcp_data.allowed_methods is None
        assert mcp_data.headers is None

    def test_create_mcp_http_stream_success(self):
        """HTTP stream形式のMCPデータ作成のテスト"""
        # Arrange
        url = "https://example.com/mcp"
        allowed_methods = ["GET", "POST"]
        headers = {"Authorization": "Bearer token"}

        # Act
        mcp_data = ModelContextProtocolData.create_mcp_http_stream(
            name="test_http_mcp",
            url=url,
            allowed_methods=allowed_methods,
            headers=headers,
        )

        # Assert
        assert mcp_data.stream_type == "streamable-http"
        assert mcp_data.url == url
        assert mcp_data.allowed_methods == allowed_methods
        assert mcp_data.headers == headers
        assert mcp_data.status == "initializing"
        assert mcp_data.command is None
        assert mcp_data.args is None

    def test_create_mcp_http_stream_minimal(self):
        """HTTP stream形式のMCPデータ作成のテスト(最小限のパラメータ)"""
        # Arrange
        url = "https://example.com/mcp"

        # Act
        mcp_data = ModelContextProtocolData.create_mcp_http_stream(
            name="test_http_mcp", url=url
        )

        # Assert
        assert mcp_data.stream_type == "streamable-http"
        assert mcp_data.url == url
        assert mcp_data.allowed_methods is None
        assert mcp_data.headers is None

    def test_name_property_stdio(self):
        """name プロパティのテスト(stdio)"""
        # Arrange
        mcp_data = ModelContextProtocolData.create_mcp_stdio(
            name="test_mcp", command="python", args=["--version"]
        )

        # Act
        name = mcp_data.name

        # Assert
        assert name == "test_mcp"

    def test_name_property_http(self):
        """name プロパティのテスト(HTTP)"""
        # Arrange
        mcp_data = ModelContextProtocolData.create_mcp_http_stream(
            name="test_http_mcp", url="https://example.com"
        )

        # Act
        name = mcp_data.name

        # Assert
        assert name == "test_http_mcp"

    def test_name_property_unknown(self):
        """name プロパティのテスト(未知のタイプ)"""
        # Arrange
        mcp_data = ModelContextProtocolData(name="unknown_mcp", stream_type="unknown")

        # Act
        name = mcp_data.name

        # Assert
        assert name == "unknown_mcp"

    def test_to_dict_stdio(self):
        """to_dict メソッドのテスト(stdio)"""
        # Arrange
        mcp_data = ModelContextProtocolData.create_mcp_stdio(
            name="test_mcp", command="python", args=["--version"]
        )
        mcp_data.status = "active"

        # Act
        result = mcp_data.to_dict()

        # Assert
        expected = {
            "name": "test_mcp",
            "stream_type": "stdio",
            "status": "active",
            "tools": [],
            "command": "python",
            "args": ["--version"],
        }
        assert result == expected

    def test_to_dict_http(self):
        """to_dict メソッドのテスト(HTTP)"""
        # Arrange
        url = "https://example.com"
        allowed_methods = ["GET"]
        headers = {"Auth": "token"}
        mcp_data = ModelContextProtocolData.create_mcp_http_stream(
            name="test_http_mcp",
            url=url,
            allowed_methods=allowed_methods,
            headers=headers,
        )

        # Act
        result = mcp_data.to_dict()

        # Assert
        expected = {
            "name": "test_http_mcp",
            "stream_type": "streamable-http",
            "status": "initializing",
            "tools": [],
            "url": url,
            "allowed_methods": allowed_methods,
            "headers": headers,
        }
        assert result == expected

    def test_to_dict_tools_empty(self):
        """to_dict_tools メソッドのテスト(空のツール)"""
        # Arrange
        mcp_data = ModelContextProtocolData.create_mcp_stdio(
            name="test_mcp", command="python", args=["--version"]
        )

        # Act
        result = mcp_data.to_dict_tools()

        # Assert
        assert result == []

    def test_to_dict_tools_with_tools(self):
        """to_dict_tools メソッドのテスト(ツール有り)"""
        # Arrange
        mcp_data = ModelContextProtocolData.create_mcp_stdio(
            name="test_mcp", command="python", args=["--version"]
        )
        mcp_data.tools = [
            {
                "name": "get_weather",
                "description": "天気を取得する",
                "inputSchema": {
                    "type": "object",
                    "properties": {"location": {"type": "string"}},
                },
            },
            {
                "name": "get_time",
                "inputSchema": {
                    "type": "object",
                    "properties": {"timezone": {"type": "string"}},
                },
            },
        ]

        # Act
        result = mcp_data.to_dict_tools()

        # Assert
        expected = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "天気を取得する",
                    "parameters": {
                        "type": "object",
                        "properties": {"location": {"type": "string"}},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_time",
                    "description": "No description.",
                    "parameters": {
                        "type": "object",
                        "properties": {"timezone": {"type": "string"}},
                    },
                },
            },
        ]
        assert result == expected

    def test_to_dict_mcp_http_stream_success(self):
        """to_dict_mcp_http_stream メソッドのテスト(成功)"""
        # Arrange
        url = "https://example.com"
        allowed_methods = ["GET", "POST"]
        headers = {"Auth": "token"}
        mcp_data = ModelContextProtocolData.create_mcp_http_stream(
            name="test_http_mcp",
            url=url,
            allowed_methods=allowed_methods,
            headers=headers,
        )

        # Act
        result = mcp_data.to_dict_mcp_http_stream()

        # Assert
        expected = {
            "type": "mcp",
            "server_url": url,
            "allowed_tools": allowed_methods,
            "headers": headers,
        }
        assert result == expected

    def test_to_dict_mcp_http_stream_wrong_type(self):
        """to_dict_mcp_http_stream メソッドのテスト(不正なタイプ)"""
        # Arrange
        mcp_data = ModelContextProtocolData.create_mcp_stdio(
            name="test_mcp", command="python", args=["--version"]
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Only 'streamable-http' is supported"):
            mcp_data.to_dict_mcp_http_stream()

    def test_direct_instantiation(self):
        """直接インスタンス化のテスト"""
        # Arrange & Act
        mcp_data = ModelContextProtocolData(
            name="test_mcp",
            stream_type="stdio",
            command="python",
            args=["--version"],
            status="active",
        )

        # Assert
        assert mcp_data.name == "test_mcp"
        assert mcp_data.stream_type == "stdio"
        assert mcp_data.command == "python"
        assert mcp_data.args == ["--version"]
        assert mcp_data.status == "active"

    def test_status_update(self):
        """ステータス更新のテスト"""
        # Arrange
        mcp_data = ModelContextProtocolData.create_mcp_stdio(
            name="test_mcp", command="python", args=["--version"]
        )

        # Act
        mcp_data.status = "active"

        # Assert
        assert mcp_data.status == "active"

    def test_tools_update(self):
        """ツール更新のテスト"""
        # Arrange
        mcp_data = ModelContextProtocolData.create_mcp_stdio(
            name="test_mcp", command="python", args=["--version"]
        )
        tools = [{"name": "test_tool", "inputSchema": {}}]

        # Act
        mcp_data.tools = tools

        # Assert
        assert mcp_data.tools == tools
