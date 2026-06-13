import pytest
from unittest.mock import MagicMock, patch
from pengent.tools.tool_utils import ToolUtils, function_tool, tool, get_package
from pengent.type.tool.tool_enum import ToolBase, ToolPackage, FunctionTool


class TestToolUtils:
    """ToolUtilsクラスのテストクラス"""

    def test_normalize_tools_with_single_tool_base(self):
        """単一のToolBaseを正規化するテスト"""
        # Arrange
        mock_tool = MagicMock(spec=ToolBase)
        mock_tool.name = "test_tool"
        tools = [mock_tool]

        # Act
        result = ToolUtils.normalize_tools(tools)

        # Assert
        assert len(result) == 1
        assert result[0] == mock_tool

    def test_normalize_tools_with_multiple_tool_base(self):
        """複数のToolBaseを正規化するテスト"""
        # Arrange
        mock_tool1 = MagicMock(spec=ToolBase)
        mock_tool1.name = "tool1"
        mock_tool2 = MagicMock(spec=ToolBase)
        mock_tool2.name = "tool2"
        tools = [mock_tool1, mock_tool2]

        # Act
        result = ToolUtils.normalize_tools(tools)

        # Assert
        assert len(result) == 2
        assert result[0] == mock_tool1
        assert result[1] == mock_tool2

    def test_normalize_tools_with_callable(self):
        """callable(関数)を正規化するテスト"""

        # Arrange
        def test_function():
            return "result"

        tools = [test_function]

        # Act
        result = ToolUtils.normalize_tools(tools)

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], FunctionTool)
        assert result[0].name == "test_function"

    def test_normalize_tools_with_enabled_tool_package(self):
        """有効なToolPackageを正規化するテスト"""
        # Arrange
        mock_tool1 = MagicMock(spec=ToolBase)
        mock_tool1.name = "tool1"
        mock_tool2 = MagicMock(spec=ToolBase)
        mock_tool2.name = "tool2"

        package = ToolPackage(
            name="test_package", tools=[mock_tool1, mock_tool2], enabled=True
        )
        tools = [package]

        # Act
        result = ToolUtils.normalize_tools(tools)

        # Assert
        assert len(result) == 2
        assert result[0] == mock_tool1
        assert result[1] == mock_tool2

    def test_normalize_tools_with_disabled_tool_package(self):
        """無効なToolPackageを正規化するテスト"""
        # Arrange
        mock_tool = MagicMock(spec=ToolBase)
        mock_tool.name = "tool1"

        package = ToolPackage(name="test_package", tools=[mock_tool], enabled=False)
        tools = [package]

        # Act
        result = ToolUtils.normalize_tools(tools)

        # Assert
        assert len(result) == 0

    def test_normalize_tools_with_nested_packages(self):
        """ネストされたToolPackageを正規化するテスト"""
        # Arrange
        mock_tool1 = MagicMock(spec=ToolBase)
        mock_tool1.name = "tool1"
        mock_tool2 = MagicMock(spec=ToolBase)
        mock_tool2.name = "tool2"

        inner_package = ToolPackage(
            name="inner_package", tools=[mock_tool2], enabled=True
        )

        outer_package = ToolPackage(
            name="outer_package", tools=[mock_tool1, inner_package], enabled=True
        )

        tools = [outer_package]

        # Act
        result = ToolUtils.normalize_tools(tools)

        # Assert
        assert len(result) == 2
        assert result[0] == mock_tool1
        assert result[1] == mock_tool2

    def test_normalize_tools_with_mixed_types(self):
        """混合型のツールを正規化するテスト"""
        # Arrange
        mock_tool = MagicMock(spec=ToolBase)
        mock_tool.name = "mock_tool"

        def test_function():
            return "result"

        tools = [mock_tool, test_function]

        # Act
        result = ToolUtils.normalize_tools(tools)

        # Assert
        assert len(result) == 2
        assert result[0] == mock_tool
        assert isinstance(result[1], FunctionTool)

    def test_normalize_tools_with_duplicate_names(self):
        """重複する名前のツールでエラーが発生することのテスト"""
        # Arrange
        mock_tool1 = MagicMock(spec=ToolBase)
        mock_tool1.name = "duplicate_name"
        mock_tool2 = MagicMock(spec=ToolBase)
        mock_tool2.name = "duplicate_name"

        tools = [mock_tool1, mock_tool2]

        # Act & Assert
        with pytest.raises(ValueError, match="Duplicate tool names"):
            ToolUtils.normalize_tools(tools)

    def test_normalize_tools_with_unsupported_type(self):
        """サポートされていない型でエラーが発生することのテスト"""
        # Arrange
        tools = ["unsupported_string"]

        # Act & Assert
        with pytest.raises(TypeError, match="Unsupported tool"):
            ToolUtils.normalize_tools(tools)

    def test_normalize_tools_empty_list(self):
        """空のリストを正規化するテスト"""
        # Arrange
        tools = []

        # Act
        result = ToolUtils.normalize_tools(tools)

        # Assert
        assert len(result) == 0
        assert result == []

    async def test_execute_tool_success(self):
        """execute_toolメソッドの成功ケーステスト"""
        # Arrange
        mock_tool = MagicMock(spec=ToolBase)
        mock_tool.run.return_value = "execution_result"
        arguments = {"param1": "value1", "param2": "value2"}

        # Act
        result = await ToolUtils.execute_tool(mock_tool, arguments)

        # Assert
        mock_tool.run.assert_called_once_with(param1="value1", param2="value2")
        assert result == "execution_result"

    async def test_execute_tool_with_no_arguments(self):
        """引数なしでexecute_toolを実行するテスト"""
        # Arrange
        mock_tool = MagicMock(spec=ToolBase)
        mock_tool.run.return_value = "result"

        # Act
        result = await ToolUtils.execute_tool(mock_tool, {})

        # Assert
        mock_tool.run.assert_called_once_with()
        assert result == "result"

    async def test_execute_tool_with_exception(self):
        """execute_toolで例外が発生することのテスト"""
        # Arrange
        mock_tool = MagicMock(spec=ToolBase)
        mock_tool.run.side_effect = RuntimeError("Tool execution failed")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Tool execution failed"):
            await ToolUtils.execute_tool(mock_tool, {})


class TestFunctionToolDecorator:
    """function_toolデコレータのテストクラス"""

    def test_function_tool_decorator(self):
        """function_toolデコレータの基本テスト"""

        # Arrange
        def sample_function(x: int, y: int) -> int:
            """サンプル関数"""
            return x + y

        # Act
        wrapped = function_tool(sample_function)

        # Assert
        assert isinstance(wrapped, FunctionTool)
        assert wrapped.__wrapped__ == sample_function
        assert wrapped.__name__ == "sample_function"
        assert wrapped.__doc__ == "サンプル関数"

    def test_function_tool_preserves_metadata(self):
        """function_toolがメタデータを保持することのテスト"""

        # Arrange
        def test_func():
            """Test documentation"""
            pass

        # Act
        wrapped = function_tool(test_func)

        # Assert
        assert wrapped.__name__ == "test_func"
        assert wrapped.__doc__ == "Test documentation"

    def test_function_tool_execution(self):
        """function_toolでラップされた関数の実行テスト"""

        # Arrange
        def multiply(a: int, b: int) -> int:
            """Multiply two numbers"""
            return a * b

        wrapped = function_tool(multiply)

        # Act
        result = wrapped.run(a=3, b=4)

        # Assert
        assert result == 12


class TestToolDecorator:
    """toolデコレータのテストクラス"""

    def test_tool_decorator_basic(self):
        """toolデコレータの基本テスト"""

        # Arrange & Act
        @tool()
        def sample_function():
            """Sample function"""
            return "result"

        # Assert
        assert hasattr(sample_function, "__pengent_tool__")
        assert sample_function.__pengent_tool__ is True
        assert hasattr(sample_function, "__pengent_tool_meta__")

    def test_tool_decorator_with_name(self):
        """toolデコレータでカスタム名を指定するテスト"""

        # Arrange & Act
        @tool(name="custom_name")
        def sample_function():
            """Sample function"""
            return "result"

        # Assert
        assert sample_function.__pengent_tool_meta__["name"] == "custom_name"

    def test_tool_decorator_with_description(self):
        """toolデコレータでカスタム説明を指定するテスト"""

        # Arrange & Act
        @tool(description="Custom description")
        def sample_function():
            """Sample function"""
            return "result"

        # Assert
        assert (
            sample_function.__pengent_tool_meta__["description"] == "Custom description"
        )

    def test_tool_decorator_with_tags(self):
        """toolデコレータでタグを指定するテスト"""

        # Arrange & Act
        @tool(tags=["tag1", "tag2", "tag3"])
        def sample_function():
            """Sample function"""
            return "result"

        # Assert
        assert sample_function.__pengent_tool_meta__["tags"] == ["tag1", "tag2", "tag3"]

    def test_tool_decorator_with_all_parameters(self):
        """toolデコレータで全パラメータを指定するテスト"""

        # Arrange & Act
        @tool(
            name="full_custom",
            description="Full custom description",
            tags=["api", "utility"],
        )
        def sample_function():
            """Sample function"""
            return "result"

        # Assert
        meta = sample_function.__pengent_tool_meta__
        assert meta["name"] == "full_custom"
        assert meta["description"] == "Full custom description"
        assert meta["tags"] == ["api", "utility"]

    def test_tool_decorator_without_parameters(self):
        """toolデコレータをパラメータなしで使用するテスト"""

        # Arrange & Act
        @tool()
        def sample_function():
            """Sample function"""
            return "result"

        # Assert
        meta = sample_function.__pengent_tool_meta__
        assert meta["name"] is None
        assert meta["description"] is None
        assert meta["tags"] == []

    def test_tool_decorator_function_still_callable(self):
        """toolデコレータ適用後も関数が呼び出し可能であることのテスト"""

        # Arrange
        @tool()
        def sample_function(x: int) -> int:
            """Sample function"""
            return x * 2

        # Act
        result = sample_function(5)

        # Assert
        assert result == 10


class TestGetPackage:
    """get_package関数のテストクラス"""

    def test_get_package_basic(self):
        """get_packageの基本テスト"""
        # Arrange
        mock_module = MagicMock()

        @tool()
        def tool_func1():
            pass

        @tool()
        def tool_func2():
            pass

        def not_a_tool():
            pass

        mock_module.__dict__ = {
            "tool_func1": tool_func1,
            "tool_func2": tool_func2,
            "not_a_tool": not_a_tool,
            "some_variable": 123,
        }

        # Act
        with patch("importlib.import_module", return_value=mock_module):
            package = get_package("test.module")

        # Assert
        assert isinstance(package, ToolPackage)
        assert len(package.tools) == 2
        assert package.name == "test.module"

    def test_get_package_with_custom_name(self):
        """get_packageでカスタム名を指定するテスト"""
        # Arrange
        mock_module = MagicMock()
        mock_module.__dict__ = {}

        # Act
        with patch("importlib.import_module", return_value=mock_module):
            package = get_package("test.module", name="custom_package_name")

        # Assert
        assert package.name == "custom_package_name"

    def test_get_package_with_description(self):
        """get_packageでdescriptionを指定するテスト"""
        # Arrange
        mock_module = MagicMock()
        mock_module.__dict__ = {}

        # Act
        with patch("importlib.import_module", return_value=mock_module):
            package = get_package("test.module", description="Package description")

        # Assert
        assert package.description == "Package description"

    def test_get_package_with_enabled_false(self):
        """get_packageでenabled=Falseを指定するテスト"""
        # Arrange
        mock_module = MagicMock()
        mock_module.__dict__ = {}

        # Act
        with patch("importlib.import_module", return_value=mock_module):
            package = get_package("test.module", enabled=False)

        # Assert
        assert package.enabled is False

    def test_get_package_with_tags(self):
        """get_packageでtagsを指定するテスト"""
        # Arrange
        mock_module = MagicMock()
        mock_module.__dict__ = {}

        # Act
        with patch("importlib.import_module", return_value=mock_module):
            package = get_package("test.module", tags=["api", "utility", "v1"])

        # Assert
        assert package.tags == ["api", "utility", "v1"]

    def test_get_package_with_all_parameters(self):
        """get_packageで全パラメータを指定するテスト"""
        # Arrange
        mock_module = MagicMock()

        @tool()
        def tool_func():
            pass

        mock_module.__dict__ = {"tool_func": tool_func}

        # Act
        with patch("importlib.import_module", return_value=mock_module):
            package = get_package(
                "test.module",
                name="full_package",
                description="Full package description",
                enabled=True,
                tags=["tag1", "tag2"],
            )

        # Assert
        assert package.name == "full_package"
        assert package.description == "Full package description"
        assert package.enabled is True
        assert package.tags == ["tag1", "tag2"]
        assert len(package.tools) == 1

    def test_get_package_empty_module(self):
        """get_packageでツールが含まれないモジュールを処理するテスト"""
        # Arrange
        mock_module = MagicMock()
        mock_module.__dict__ = {"some_variable": 123, "regular_function": lambda: None}

        # Act
        with patch("importlib.import_module", return_value=mock_module):
            package = get_package("test.module")

        # Assert
        assert len(package.tools) == 0

    def test_get_package_filters_non_callable(self):
        """get_packageが非callableオブジェクトをフィルタリングすることのテスト"""
        # Arrange
        mock_module = MagicMock()

        @tool()
        def valid_tool():
            pass

        mock_module.__dict__ = {
            "valid_tool": valid_tool,
            "string_var": "not callable",
            "number_var": 42,
            "list_var": [1, 2, 3],
        }

        # Act
        with patch("importlib.import_module", return_value=mock_module):
            package = get_package("test.module")

        # Assert
        assert len(package.tools) == 1
        assert package.tools[0] == valid_tool
