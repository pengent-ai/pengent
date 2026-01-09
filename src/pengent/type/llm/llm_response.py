from typing import Dict, Optional, List, Union
from dataclasses import dataclass, field
from .llm_message import LLMMessageTool
from pydantic import BaseModel


@dataclass
class ResponseText:
    """テキストレスポンスデータクラス"""

    text: str
    type: str = "text"


@dataclass
class ResponseObject:
    """オブジェクトレスポンスデータクラス"""

    content: Union[Dict, BaseModel]
    type: str = "object"


@dataclass
class ResponseImage:
    """画像レスポンスデータクラス"""

    url: Optional[str] = None
    base64_data: Optional[str] = None
    type: str = "image"


@dataclass
class ResponseTools:
    """ツールレスポンスデータクラス"""

    tools: List[LLMMessageTool]  # { "name": ..., "arguments": ... }
    type: str = "tools"

    @classmethod
    def from_dict(cls, data: Union[dict, list]) -> "ResponseTools":
        if isinstance(data, list):  # 直接リストが渡ってきたとき
            tools = [LLMMessageTool.from_dict(t) for t in data]
        elif isinstance(data, dict):
            tools = [LLMMessageTool.from_dict(t) for t in data.get("tools", [])]
        else:
            raise ValueError("Invalid tool data format")
        # tools = [LLMMessageTool.from_dict(t) for t in data.get("tools", [])]
        return cls(tools=tools)


ResponseContent = Union[ResponseText, ResponseImage, ResponseTools]


@dataclass
class LLMResponseTokenUsage:
    """LLMレスポンストークン使用量データクラス"""

    input_tokens: int
    output_tokens: int
    total_tokens: int
    cache_creation_input_tokens: Optional[int] = None
    cache_read_input_tokens: Optional[int] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> "LLMResponseTokenUsage":
        return cls(
            input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
            total_tokens=data.get(
                "total_tokens",
                data.get("input_tokens", 0) + data.get("output_tokens", 0),
            ),
            cache_creation_input_tokens=data.get("cache_creation_input_tokens"),
            cache_read_input_tokens=data.get("cache_read_input_tokens"),
        )


@dataclass
class LLMResponse:
    """
    このクラスは、LLMからのレスポンスを格納するためのデータ構造を提供します。
    """

    content: List[ResponseContent] = field(default_factory=list)
    token_usage: LLMResponseTokenUsage = None
    metadata: dict = field(default_factory=dict)

    def get_message(self):
        """
        レスポンスからメッセージを取得するメソッド
        :return: メッセージのリスト
        """
        for item in self.content:
            if isinstance(item, ResponseText):
                return item.text
        return None

    def is_message(self) -> bool:
        """
        レスポンスからメッセージが存在するか確認するメソッド
        """
        for item in self.content:
            if isinstance(item, ResponseText):
                return True
        return False

    def get_object(self):
        """
        レスポンスからオブジェクトを取得するメソッド
        :return: オブジェクトのリスト
        """
        for item in self.content:
            if isinstance(item, ResponseObject):
                return item.text
        return None

    def is_object(self) -> bool:
        """
        レスポンスからメッセージが存在するか確認するメソッド
        """
        for item in self.content:
            if isinstance(item, ResponseObject):
                return True
        return False

    def get_tools(self):
        """
        レスポンスからメッセージを取得するメソッド
        :return: メッセージのリスト
        """
        for item in self.content:
            if isinstance(item, ResponseTools):
                return item.tools
        return None

    def add_content_text(self, text: str):
        """
        レスポンスにテキストコンテンツを追加するメソッド
        :param text: 追加するテキスト
        """
        self.content.append(ResponseText(text=text))

    def add_content_object(self, obj: Union[Dict, BaseModel]):
        """
        レスポンスにオブジェクトコンテンツを追加するメソッド
        :param obj: 追加するオブジェクト
        """
        self.content.append(ResponseObject(content=obj))

    def add_content_tools(self, tools: List[dict]):
        """
        レスポンスにツールコンテンツを追加するメソッド
        :param tools: 追加するツールのリスト
        """
        self.content.append(ResponseTools.from_dict(tools))
