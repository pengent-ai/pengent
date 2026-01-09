import importlib
from types import ModuleType
from typing import Any, Callable, Optional, Union
from functools import update_wrapper
from ..type.tool.tool_enum import (
    ToolUnion,
    ToolBase,
    ToolPackage,
    FunctionTool,
    ToolContext,
)
from .mcp.mcp_tool_package import McpToolPackage


class ToolUtils:
    """ツールユーティリティクラス"""

    @staticmethod
    def normalize_tools(
        tools: list[Union[ToolUnion, McpToolPackage]],
    ) -> list[ToolBase]:
        """ツールのリストを正規化する関数"""
        output: list[ToolBase] = []
        for tool in tools:
            if isinstance(tool, ToolPackage):
                if not tool.enabled:
                    continue
                output.extend(ToolUtils.normalize_tools(tool.tools))
            elif isinstance(tool, McpToolPackage):
                if tool.mcp_data.status != "active":
                    continue
                output.extend(tool.tools)
            elif isinstance(tool, ToolBase):
                output.append(tool)
            elif callable(tool):
                output.append(FunctionTool(tool))
            else:
                raise TypeError(f"Unsupported tool: {type(tool)}")

        # 重複チェック
        names = [tool.name for tool in output]
        duplicated = {name for name in names if names.count(name) > 1}
        if duplicated:
            raise ValueError(f"Duplicate tool names: {duplicated}")

        return output

    @staticmethod
    def execute_tool(
        tool: ToolBase,
        parguments: dict,
        *,
        context: Optional[Any] = None,
    ) -> Any:
        """ツール名でツールを実行する関数"""
        kwargs = dict(parguments or {})

        if isinstance(tool, FunctionTool):
            if tool.has_tool_context():
                parguments["tool_context"] = ToolContext.create(context)
            return tool.run(**kwargs)

        return tool.run(**kwargs)


def function_tool(fn: Callable) -> "FunctionTool":
    """
    関数をFunctionToolにラップするデコレータ
    """
    ft = FunctionTool(fn)
    ft.__wrapped__ = fn  # 元関数参照(重要)
    update_wrapper(ft, fn)  # __name__, __doc__ 等のメタを寄せる
    return ft


def tool(
    *,
    tags: Optional[list[str]] = None,
    name: str | None = None,
    description: str | None = None,
):
    """get_package用の収集に使う関数デコレータ"""

    def _wrap(fn: Callable) -> Callable:
        fn.__pengent_tool__ = True
        fn.__pengent_tool_meta__ = {
            "tags": tags or [],
            "name": name,  # Noneなら関数名を使う
            "description": description,  # Noneなら doc_summary を使う
        }
        return fn

    return _wrap


def get_package(
    module_path: str,
    *,
    name: str = "",
    description: str = "",
    enabled: bool = True,
    tags: list[str] | None = None,
) -> ToolPackage:
    mod: ModuleType = importlib.import_module(module_path)
    tools: list[ToolUnion] = []
    for obj in vars(mod).values():
        if callable(obj) and getattr(obj, "__pengent_tool__", False):
            tools.append(obj)

    return ToolPackage(
        name=name or module_path,
        description=description,
        enabled=enabled,
        tags=tags or [],
        tools=tools,
    )
