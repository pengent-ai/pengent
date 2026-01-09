import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pengent.tools.mcp.mcp_client import ModelContextProtocolClient
from pengent.tools.mcp.mcp_data import ModelContextProtocolData


class TestModelContextProtocolClient:
    """ModelContextProtocolClientクラスのテストクラス"""

    def test_init_stdio(self):
        """初期化のテスト(stdio)"""
        # Arrange
        mcp_data = ModelContextProtocolData.create_mcp_stdio(
            name="test_mcp", command="python", args=["--version"]
        )

        # Act
        client = ModelContextProtocolClient(mcp_data)

        # Assert
        assert client.mcp_data == mcp_data
        assert client.session is None

    def test_init_http(self):
        """初期化のテスト(HTTP)"""
        # Arrange
        mcp_data = ModelContextProtocolData.create_mcp_http_stream(
            name="test_http_mcp", url="https://example.com"
        )

        # Act
        client = ModelContextProtocolClient(mcp_data)

        # Assert
        assert client.mcp_data == mcp_data
        assert client.session is None

    @pytest.mark.asyncio
    @patch("pengent.tools.mcp.mcp_client.stdio_client")
    @patch("pengent.tools.mcp.mcp_client.ClientSession")
    async def test_connect_stdio_success(self, mock_client_session, mock_stdio_client):
        """stdio接続のテスト(成功)"""
        # Arrange
        mcp_data = ModelContextProtocolData.create_mcp_stdio(
            name="test_mcp", command="python", args=["--version"]
        )
        client = ModelContextProtocolClient(mcp_data)

        # Mock設定
        mock_read_stream = MagicMock()
        mock_write_stream = MagicMock()
        mock_stdio_client.return_value.__aenter__.return_value = (
            mock_read_stream,
            mock_write_stream,
        )

        mock_session = AsyncMock()
        mock_client_session.return_value.__aenter__.return_value = mock_session

        # Act
        async with client.connect() as connected_client:
            # Assert
            assert connected_client == client
            assert client.session == mock_session
            mock_session.initialize.assert_called_once()

        # 接続終了後のテスト
        assert client.session is None

    @pytest.mark.asyncio
    @patch("pengent.tools.mcp.mcp_client.streamablehttp_client")
    @patch("pengent.tools.mcp.mcp_client.ClientSession")
    async def test_connect_http_success(
        self, mock_client_session, mock_streamablehttp_client
    ):
        """HTTP接続のテスト(成功)"""
        # Arrange
        mcp_data = ModelContextProtocolData.create_mcp_http_stream(
            name="test_http_mcp", url="https://example.com"
        )
        client = ModelContextProtocolClient(mcp_data)

        # Mock設定
        mock_read_stream = MagicMock()
        mock_write_stream = MagicMock()
        mock_get_session_id = MagicMock()
        mock_streamablehttp_client.return_value.__aenter__.return_value = (
            mock_read_stream,
            mock_write_stream,
            mock_get_session_id,
        )

        mock_session = AsyncMock()
        mock_client_session.return_value.__aenter__.return_value = mock_session

        # Act
        async with client.connect() as connected_client:
            # Assert
            assert connected_client == client
            assert client.session == mock_session
            mock_session.initialize.assert_called_once()

        # 接続終了後のテスト
        assert client.session is None

    @pytest.mark.asyncio
    async def test_connect_unsupported_stream_type(self):
        """未サポートのストリームタイプのテスト"""
        # Arrange
        mcp_data = ModelContextProtocolData(name="unknown_mcp", stream_type="unknown")
        client = ModelContextProtocolClient(mcp_data)

        # Act & Assert
        with pytest.raises(
            NotImplementedError, match="Unsupported stream type: unknown"
        ):
            async with client.connect():
                pass

    @pytest.mark.asyncio
    async def test_list_tools_success(self):
        """ツール一覧取得のテスト(成功)"""
        # Arrange
        mcp_data = ModelContextProtocolData.create_mcp_stdio(
            name="test_mcp", command="python", args=["--version"]
        )
        client = ModelContextProtocolClient(mcp_data)

        # Mock設定
        mock_session = AsyncMock()
        mock_tool1 = MagicMock()
        mock_tool1.model_dump.return_value = {
            "name": "tool1",
            "description": "Test tool 1",
            "inputSchema": {"type": "object"},
        }
        mock_tool2 = MagicMock()
        mock_tool2.model_dump.return_value = {
            "name": "tool2",
            "description": "Test tool 2",
            "inputSchema": {"type": "object"},
        }

        mock_response = MagicMock()
        mock_response.tools = [mock_tool1, mock_tool2]
        mock_session.list_tools.return_value = mock_response

        client.session = mock_session

        # Act
        result = await client.list_tools()

        # Assert
        expected = [
            {
                "name": "tool1",
                "description": "Test tool 1",
                "inputSchema": {"type": "object"},
            },
            {
                "name": "tool2",
                "description": "Test tool 2",
                "inputSchema": {"type": "object"},
            },
        ]
        assert result == expected
        mock_session.list_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tools_no_session(self):
        """ツール一覧取得のテスト(セッションなし)"""
        # Arrange
        mcp_data = ModelContextProtocolData.create_mcp_stdio(
            name="test_mcp", command="python", args=["--version"]
        )
        client = ModelContextProtocolClient(mcp_data)

        # Act & Assert
        with pytest.raises(RuntimeError, match="Session not initialized"):
            await client.list_tools()

    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """ツール呼び出しのテスト(成功)"""
        # Arrange
        mcp_data = ModelContextProtocolData.create_mcp_stdio(
            name="test_mcp", command="python", args=["--version"]
        )
        client = ModelContextProtocolClient(mcp_data)

        # Mock設定
        mock_session = AsyncMock()
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "result": "success",
            "data": "tool executed",
        }
        mock_session.call_tool.return_value = mock_response

        client.session = mock_session

        # Act
        result = await client.call_tool("test_tool", {"param": "value"})

        # Assert
        expected = {"result": "success", "data": "tool executed"}
        assert result == expected
        mock_session.call_tool.assert_called_once_with("test_tool", {"param": "value"})

    @pytest.mark.asyncio
    async def test_call_tool_no_session(self):
        """ツール呼び出しのテスト(セッションなし)"""
        # Arrange
        mcp_data = ModelContextProtocolData.create_mcp_stdio(
            name="test_mcp", command="python", args=["--version"]
        )
        client = ModelContextProtocolClient(mcp_data)

        # Act & Assert
        with pytest.raises(RuntimeError, match="Session not initialized"):
            await client.call_tool("test_tool", {"param": "value"})

    @pytest.mark.asyncio
    async def test_ping_success(self):
        """ping のテスト(成功)"""
        # Arrange
        mcp_data = ModelContextProtocolData.create_mcp_stdio(
            name="test_mcp", command="python", args=["--version"]
        )
        client = ModelContextProtocolClient(mcp_data)

        # Mock設定
        mock_session = AsyncMock()
        client.session = mock_session

        # Act
        result = await client.ping()

        # Assert
        assert result is None
        mock_session.send_ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_ping_no_session(self):
        """ping のテスト(セッションなし)"""
        # Arrange
        mcp_data = ModelContextProtocolData.create_mcp_stdio(
            name="test_mcp", command="python", args=["--version"]
        )
        client = ModelContextProtocolClient(mcp_data)

        # Act & Assert
        with pytest.raises(RuntimeError, match="Session not initialized"):
            await client.ping()

    @pytest.mark.asyncio
    @patch("pengent.tools.mcp.mcp_client.stdio_client")
    @patch("pengent.tools.mcp.mcp_client.ClientSession")
    async def test_connect_stdio_with_params(
        self, mock_client_session, mock_stdio_client
    ):
        """stdio接続パラメータのテスト"""
        # Arrange
        command = "python"
        args = ["--version", "--help"]
        mcp_data = ModelContextProtocolData.create_mcp_stdio(
            name="test_mcp", command=command, args=args
        )
        client = ModelContextProtocolClient(mcp_data)

        # Mock設定
        mock_read_stream = MagicMock()
        mock_write_stream = MagicMock()
        mock_stdio_client.return_value.__aenter__.return_value = (
            mock_read_stream,
            mock_write_stream,
        )

        mock_session = AsyncMock()
        mock_client_session.return_value.__aenter__.return_value = mock_session

        # Act
        async with client.connect():
            pass

        # Assert
        # StdioServerParametersが正しいパラメータで呼び出されているか確認
        mock_stdio_client.assert_called_once()
        call_args = mock_stdio_client.call_args[0][0]
        assert call_args.command == command
        assert call_args.args == args

    @pytest.mark.asyncio
    @patch("pengent.tools.mcp.mcp_client.streamablehttp_client")
    @patch("pengent.tools.mcp.mcp_client.ClientSession")
    async def test_connect_http_with_url(
        self, mock_client_session, mock_streamablehttp_client
    ):
        """HTTP接続URLのテスト"""
        # Arrange
        url = "https://example.com/mcp"
        mcp_data = ModelContextProtocolData.create_mcp_http_stream(
            name="test_http_mcp", url=url
        )
        client = ModelContextProtocolClient(mcp_data)

        # Mock設定
        mock_read_stream = MagicMock()
        mock_write_stream = MagicMock()
        mock_get_session_id = MagicMock()
        mock_streamablehttp_client.return_value.__aenter__.return_value = (
            mock_read_stream,
            mock_write_stream,
            mock_get_session_id,
        )

        mock_session = AsyncMock()
        mock_client_session.return_value.__aenter__.return_value = mock_session

        # Act
        async with client.connect():
            pass

        # Assert
        mock_streamablehttp_client.assert_called_once_with(url)
