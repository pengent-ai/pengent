from copy import deepcopy
import inspect
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    Any,
    Union,
    Callable,
    get_origin,
    get_args,
    TypeAlias,
    Optional,
)
from ..agent.agent_enum import ExecutionContext
from ...core.artifacts.artifact_service import (
    ExecutionArtifactService,
)
from ...core.artifacts.artifact import ArtifactBase


ToolUnion: TypeAlias = Union[Callable, "ToolBase", "ToolPackage"]
# from ..llm_message import LLMClientType


class ToolBase(ABC):
    """
    ツールの基底クラス
    """

    name: str
    description: str

    @abstractmethod
    def parameters_schema(self) -> dict:
        pass

    @abstractmethod
    def run(self, **kwargs) -> Any:
        pass

    def dump(self) -> dict:
        """OpenAIやGeminiのツールフォーマットに変換するメソッド"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema(),
            },
        }


def doc_summary(fn) -> str:
    """関数のドキュメンテーション文字列から概要を抽出するヘルパー関数"""
    # PEP257に沿ってインデントを正規化
    doc = inspect.getdoc(fn) or ""
    # 先頭の空行を落として、最初の非空行だけを取る
    for line in doc.splitlines():
        s = line.strip()
        if s:
            return s
    return ""


def _parse_docstring(fn) -> dict[str, dict]:
    """
    docstringをパースして、各セクション（Args, Returns, Raises等）の情報を抽出する
    Google形式に対応

    Returns:
        {section_name: {param_name: description}} の辞書
    """
    doc = inspect.getdoc(fn) or ""
    sections = {}
    current_section = None
    section_content = {}
    last_param_indent = None
    last_param_key = None

    lines = doc.split("\n")

    for _i, line in enumerate(lines):
        # セクションヘッダー判定（"Section:" の形式、行頭から）
        section_match = re.match(r"^([A-Z][a-zA-Z\s]+?):\s*$", line)
        if section_match:
            # 前のセクションを保存
            if current_section and section_content:
                sections[current_section] = section_content

            current_section = section_match.group(1).strip().lower()
            section_content = {}
            last_param_indent = None
            last_param_key = None
            continue

        if current_section:
            stripped = line.lstrip()
            if not stripped:
                continue

            # インデントされた行のみ処理
            if line[0].isspace():
                line_indent = len(line) - len(stripped)

                # パラメータ行の判定（Google形式）
                # query: description
                # query(str): description
                param_match = re.match(
                    r"^([a-zA-Z_]\w*)(\([^)]*\))?\s*:\s+(.*)", stripped
                )
                if param_match:
                    param_name = param_match.group(1)
                    desc = param_match.group(3)
                    last_param_indent = line_indent
                    last_param_key = param_name
                    section_content[param_name] = desc.strip()
                elif (
                    last_param_indent is not None
                    and line_indent > last_param_indent
                    and last_param_key
                ):
                    # パラメータ定義でない行だが、
                    # 最後のパラメータより深いインデント = 説明の継続
                    section_content[last_param_key] += " " + stripped

    # 最後のセクションを保存
    if current_section and section_content:
        sections[current_section] = section_content

    return sections


def _python_type_to_schema(tp) -> dict:
    # 未指定 or Any
    if tp is Any or tp is None:
        return {"type": "string"}

    # 基本型
    if tp is str:
        return {"type": "string"}
    if tp is int:
        return {"type": "integer"}
    if tp is float:
        return {"type": "number"}
    if tp is bool:
        return {"type": "boolean"}

    origin = get_origin(tp)
    args = get_args(tp)

    # Optional[T] / Union[T, None]
    if origin is Union and type(None) in args:
        non_none = [arg for arg in args if arg is not type(None)][0]
        schema = _python_type_to_schema(non_none)
        # OpenAI系は nullable を理解する
        schema["nullable"] = True
        return schema

    # list[T]
    if origin is list:
        item_type = args[0] if args else Any
        return {
            "type": "array",
            "items": _python_type_to_schema(item_type),
        }

    # dict[str, T]
    if origin is dict:
        value_type = args[1] if len(args) == 2 else Any
        return {
            "type": "object",
            "additionalProperties": _python_type_to_schema(value_type),
        }

    # fallback(壊れない最優先)
    return {"type": "string"}


def parameters_schema_from_fn(fn, exclude: Optional[set] = None) -> list[dict, list]:
    sig = inspect.signature(fn)
    props = {}
    required = []
    _internal_args = []

    if exclude is None:
        exclude = set()

    # docstringをパース
    parsed_doc = _parse_docstring(fn)
    param_docs = parsed_doc.get("args", {})

    for name, param in sig.parameters.items():
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue

        # ツールコンテキストは内部処理要なのでスキップする
        if name in exclude:
            _internal_args.append(name)
            continue

        schema = _python_type_to_schema(param.annotation)

        # docstringから説明を追加
        if name in param_docs:
            schema["description"] = param_docs[name]

        if param.default is not inspect.Parameter.empty:
            schema["default"] = param.default
        else:
            required.append(name)

        props[name] = schema

    return {
        "type": "object",
        "properties": props,
        "required": required,
        "additionalProperties": False,
    }, _internal_args


class FunctionTool(ToolBase):
    """
    関数をツールとしてラップするクラス
    """

    def __init__(self, fn):
        self.fn = fn
        self.name = fn.__name__
        self.description = doc_summary(fn)

        _parameters_schema, _internal_args = parameters_schema_from_fn(
            fn,
            exclude={"tool_context"},
        )
        self._parameters_schema = _parameters_schema
        self._internal_args = _internal_args

    def has_tool_context(self) -> bool:
        return "tool_context" in self._internal_args

    def parameters_schema(self) -> dict:
        return self._parameters_schema

    def run(self, **kwargs) -> Any:
        return self.fn(**kwargs)

    def __call__(self, **kwargs) -> Any:
        return self.run(**kwargs)


@dataclass()
class ToolPackage:
    """ツールパッケージのデータクラス"""

    tools: list[ToolUnion]
    name: str = ""
    description: str = ""
    enabled: bool = True
    tags: list[str] = field(default_factory=list)


@dataclass()
class ToolContext:
    """ツール実行時のコンテキスト情報"""

    session_id: str  # セッションID
    user_id: str  # ユーザーID
    state: Optional[dict]  # セッション状態
    _state_delta: dict
    _artifact_service: Optional[ExecutionArtifactService] = field(default=None)

    @classmethod
    def create(cls, context: ExecutionContext) -> "ToolContext":
        """ExecutionContextオブジェクトからToolContextを作成するクラスメソッド"""
        return cls(
            session_id=context.session_id,
            user_id=context.user_id,
            state=deepcopy(context.state) if context.state else {},
            _state_delta=context._state_delta,
            _artifact_service=context._artifact_service,
        )

    def get_state_delta(self) -> Optional[dict]:
        """状態の変更点を取得するメソッド"""
        return self._state_delta

    def set_state_delta(self, key: str, value: any):
        """状態の変更点を設定するメソッド"""
        self._state_delta[key] = value

    def update_state_delta(self, delta: dict):
        """状態の変更点を更新するメソッド"""
        self._state_delta.update(delta)

    def save_artifact(
        self,
        filename: str,
        artifact: ArtifactBase,
        custom_meta: dict = None,
    ) -> int:
        """アーティファクトを保存するメソッド"""
        if not self._artifact_service:
            return None
        return self._artifact_service.save(
            file_name=filename,
            artifact=artifact,
            custom_meta=custom_meta,
        )

    def load_artifact(
        self,
        filename: str,
        version: int = None,
    ) -> Optional[ArtifactBase]:
        """アーティファクトを読み込むメソッド"""
        if not self._artifact_service:
            return None
        return self._artifact_service.load(
            file_name=filename,
            version=version,
        )
