import pytest
from pengent.type.tool.tool_enum import (
    _parse_docstring,
    parameters_schema_from_fn,
    FunctionTool,
)


class TestParseDocstring:
    """docstringパーサーのテスト"""

    def test_parse_basic_args(self):
        """基本的なArgsセクションのパース"""

        def example_func(query: str, limit: int = 10):
            """
            検索を実行する

            Args:
                query: 検索キーワード
                limit: 最大結果数
            """
            pass

        result = _parse_docstring(example_func)
        assert "args" in result
        assert result["args"]["query"] == "検索キーワード"
        assert result["args"]["limit"] == "最大結果数"

    def test_parse_args_with_type_info(self):
        """型情報付きのArgsセクションのパース"""

        def example_func(query: str, limit: int = 10):
            """
            検索を実行する

            Args:
                query(str): 検索キーワード
                limit(int): 最大結果数
            """
            pass

        result = _parse_docstring(example_func)
        assert result["args"]["query"] == "検索キーワード"
        assert result["args"]["limit"] == "最大結果数"

    def test_parse_multiple_sections(self):
        """複数セクションのパース"""

        def example_func(query: str):
            """
            検索を実行する

            Args:
                query: 検索キーワード

            Returns:
                result: 検索結果のリスト

            Raises:
                error: クエリが空の場合
            """
            pass

        result = _parse_docstring(example_func)
        assert "args" in result
        assert "returns" in result
        assert "raises" in result
        assert result["args"]["query"] == "検索キーワード"
        assert result["returns"]["result"] == "検索結果のリスト"
        assert result["raises"]["error"] == "クエリが空の場合"

    def test_parse_multiline_description(self):
        """複数行の説明のパース"""

        def example_func(query: str):
            """
            検索を実行する

            Args:
                query: 検索キーワード
                    複数の単語をスペースで区切ることで
                    AND検索が可能です
            """
            pass

        result = _parse_docstring(example_func)
        expected = "検索キーワード 複数の単語をスペースで区切ることで AND検索が可能です"
        assert result["args"]["query"] == expected

    def test_parse_empty_docstring(self):
        """ドキュメンテーションなしの関数"""

        def example_func(query: str):
            pass

        result = _parse_docstring(example_func)
        assert result == {}

    def test_parse_no_args_section(self):
        """Argsセクションがない場合"""

        def example_func(query: str):
            """
            検索を実行する

            Returns:
                result: 検索結果のリスト
            """
            pass

        result = _parse_docstring(example_func)
        assert "args" not in result
        assert "returns" in result


class TestParametersSchemaFromFn:
    """parameters_schema_from_fn関数のテスト"""

    def test_basic_parameters_schema(self):
        """基本的なパラメータスキーマの生成"""

        def example_func(query: str, limit: int = 10):
            """
            検索を実行する

            Args:
                quer (str): 検索キーワード
                limit: 最大結果数
            """
            pass

        schema, internal_args = parameters_schema_from_fn(example_func)

        assert schema["type"] == "object"
        assert "query" in schema["properties"]
        assert "limit" in schema["properties"]
        assert schema["required"] == ["query"]
        assert schema["additionalProperties"] is False

    def test_parameter_descriptions(self):
        """パラメータの説明がスキーマに含まれることを確認"""

        def example_func(query: str, limit: int = 10):
            """
            検索を実行する

            Args:
                query: 検索キーワード
                limit: 最大結果数
            """
            pass

        schema, _ = parameters_schema_from_fn(example_func)

        assert schema["properties"]["query"]["description"] == "検索キーワード"
        assert schema["properties"]["limit"]["description"] == "最大結果数"

    def test_parameter_types(self):
        """パラメータの型がスキーマに正しく反映される"""

        def example_func(
            query: str,
            limit: int,
            max_score: float,
            is_active: bool,
        ):
            """
            検索を実行する

            Args:
                query: 検索キーワード
                limit: 最大結果数
                max_score: 最大スコア
                is_active: アクティブフラグ
            """
            pass

        schema, _ = parameters_schema_from_fn(example_func)

        assert schema["properties"]["query"]["type"] == "string"
        assert schema["properties"]["limit"]["type"] == "integer"
        assert schema["properties"]["max_score"]["type"] == "number"
        assert schema["properties"]["is_active"]["type"] == "boolean"

    def test_parameter_defaults(self):
        """デフォルト値がスキーマに含まれることを確認"""

        def example_func(query: str, limit: int = 10, timeout: float = 5.0):
            """
            検索を実行する

            Args:
                query: 検索キーワード
                limit: 最大結果数
                timeout: タイムアウト時間
            """
            pass

        schema, _ = parameters_schema_from_fn(example_func)

        assert schema["properties"]["limit"]["default"] == 10
        assert schema["properties"]["timeout"]["default"] == 5.0
        assert "default" not in schema["properties"]["query"]

    def test_exclude_parameters(self):
        """除外パラメータがスキーマから除外される"""

        def example_func(query: str, tool_context):
            """
            検索を実行する

            Args:
                query: 検索キーワード
                tool_context: ツールコンテキスト
            """
            pass

        schema, internal_args = parameters_schema_from_fn(
            example_func, exclude={"tool_context"}
        )

        assert "query" in schema["properties"]
        assert "tool_context" not in schema["properties"]
        assert "tool_context" in internal_args
        assert schema["required"] == ["query"]

    def test_optional_parameters(self):
        """Optional型のパラメータ"""
        from typing import Optional

        def example_func(query: str, filter: Optional[str] = None):
            """
            検索を実行する

            Args:
                query: 検索キーワード
                filter: フィルター条件
            """
            pass

        schema, _ = parameters_schema_from_fn(example_func)

        assert schema["properties"]["filter"]["type"] == "string"
        assert schema["properties"]["filter"]["nullable"] is True

    def test_list_parameters(self):
        """List型のパラメータ"""
        from typing import List

        def example_func(tags: List[str]):
            """
            検索を実行する

            Args:
                tags: タグのリスト
            """
            pass

        schema, _ = parameters_schema_from_fn(example_func)

        assert schema["properties"]["tags"]["type"] == "array"
        assert schema["properties"]["tags"]["items"]["type"] == "string"

    def test_dict_parameters(self):
        """dict型のパラメータ"""
        from typing import Dict

        def example_func(metadata: Dict[str, str]):
            """
            検索を実行する

            Args:
                metadata: メタデータ
            """
            pass

        schema, _ = parameters_schema_from_fn(example_func)

        assert schema["properties"]["metadata"]["type"] == "object"
        assert (
            schema["properties"]["metadata"]["additionalProperties"]["type"] == "string"
        )

    def test_no_docstring(self):
        """ドキュメンテーションなしの関数"""

        def example_func(query: str, limit: int = 10):
            pass

        schema, _ = parameters_schema_from_fn(example_func)

        # スキーマは生成されるが、descriptionはない
        assert "query" in schema["properties"]
        assert "description" not in schema["properties"]["query"]


class TestFunctionTool:
    """FunctionToolクラスのテスト"""

    def test_function_tool_with_descriptions(self):
        """説明付きのFunctionTool"""

        def search(query: str, limit: int = 10):
            """
            ウェブを検索する

            Args:
                query: 検索キーワード
                limit: 最大結果数
            """
            return f"Search results for {query}"

        tool = FunctionTool(search)

        assert tool.name == "search"
        assert tool.description == "ウェブを検索する"

        schema = tool.parameters_schema()
        assert schema["properties"]["query"]["description"] == "検索キーワード"
        assert schema["properties"]["limit"]["description"] == "最大結果数"

    def test_function_tool_dump(self):
        """FunctionToolのdump出力"""

        def search(query: str, limit: int = 10):
            """
            ウェブを検索する

            Args:
                query: 検索キーワード
                limit: 最大結果数
            """
            return f"Search results for {query}"

        tool = FunctionTool(search)
        dumped = tool.dump()

        assert dumped["type"] == "function"
        assert dumped["function"]["name"] == "search"
        assert dumped["function"]["description"] == "ウェブを検索する"
        assert "parameters" in dumped["function"]
        assert (
            dumped["function"]["parameters"]["properties"]["query"]["description"]
            == "検索キーワード"
        )

    def test_function_tool_run(self):
        """FunctionToolの実行"""

        def add(a: int, b: int):
            """
            2つの数値を足す

            Args:
                a: 最初の数値
                b: 2番目の数値
            """
            return a + b

        tool = FunctionTool(add)
        result = tool.run(a=5, b=3)

        assert result == 8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
