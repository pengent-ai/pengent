import json
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from .llm_type_enum import LLMClientType, LLMMessageRole

from ...lib.common import (
    encode_base64_from_binary,
    encode_base64_from_file,
)


@dataclass
class LLMMessageToolFunction:
    """
    LLMMessageContensTextクラスは、LLMから依頼のあったToolsの情報を保持するクラス
    """

    name: str
    arguments: Optional[dict] = None

    def to_dict(self) -> dict:
        data = {"name": self.name, "arguments": self.arguments}
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class LLMMessageTool:
    """
    LLMMessageContensTextクラスは、LLMから依頼のあったToolsの情報を保持するクラス
    """

    function: LLMMessageToolFunction
    type: str = "function"
    id: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "type": self.type,
            "function": self.function.to_dict(),
            "meta_data": self.meta_data,
        }
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> "LLMMessageTool":
        return cls(
            id=data.get("id"),
            type=data.get("type", "function"),
            function=LLMMessageToolFunction(
                name=data["function"]["name"],
                arguments=data["function"].get("arguments"),
            ),
            meta_data=data.get("meta_data"),
        )

    def to_format_type(self, llm_type=LLMClientType.OPENAI.value) -> dict:
        if llm_type == LLMClientType.OPENAI.value:
            return {
                "id": self.id,
                "type": self.type,
                "function": {
                    "name": self.function.name,
                    "arguments": json.dumps(
                        self.function.arguments or {}
                    ),  # ✅ ここだけ変える！
                },
            }
        elif llm_type == LLMClientType.ANTHROPIC.value:
            fucntion = self.function.to_dict()
            return {
                "id": self.id,
                "type": "tool_use",
                "name": fucntion["name"],
                "input": fucntion["arguments"],
            }
        elif llm_type == LLMClientType.GEMINI.value:
            fucntion = self.function.to_dict()
            return {
                "functionCall": {
                    "name": fucntion["name"],
                    "args": fucntion["arguments"],
                }
            }
        else:
            raise NotImplementedError(
                f"LLM type '{llm_type}' does not support tool calls."
            )


@dataclass
class LLMMessageContentImage:
    """
    LLMMessageContentImageクラスは、LLMメッセージの画像コンテンツ
    """

    url: Optional[str] = None
    base64_data: Optional[str] = None
    mime_type: Optional[str] = None

    def __repr__(self):
        if self.base64_data:
            # base64データを20文字に短縮して表示
            truncated = (
                self.base64_data[:20] + "..."
                if len(self.base64_data) > 20
                else self.base64_data
            )
            return f"LLMMessageContentImage(base64_data='{truncated}')"
        elif self.url:
            return f"LLMMessageContentImage(url='{self.url}')"
        return "LLMMessageContentImage()"

    def base64_data_url(self) -> Optional[str]:
        """Base64データURLを取得する"""
        if self.base64_data:
            if self.mime_type:
                return f"data:{self.mime_type};base64,{self.base64_data}"
            else:
                return f"data:application/octet-stream;base64,{self.base64_data}"
        return None

    @classmethod
    def create_content_image_from_data(
        cls,
        data: bytes,
        mime_type: str = None,
        file_path: str = None,
    ) -> "LLMMessageContentImage":
        base64_data, mime_type = encode_base64_from_binary(data, mime_type, file_path)
        return cls(base64_data=base64_data, mime_type=mime_type)

    @classmethod
    def create_content_image_from_file(
        cls,
        file_path: str,
        mime_type: str = None,
    ) -> "LLMMessageContentImage":
        base64_data, mime_type = encode_base64_from_file(file_path, mime_type)
        return cls(base64_data=base64_data, mime_type=mime_type)

    def to_dict(self) -> dict:
        data = {
            "url": self.url,
            "base64_data": self.base64_data,
            "mime_type": self.mime_type,
        }
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class LLMMessageContent:
    """
    LLMMessageContentクラスは、LLMメッセージのコンテンツ
    を表します。このクラスは、テキストや画像などの異なるタイプの
    コンテンツを扱うためのデータ構造を提供します。
    """

    type: str
    text: Optional[str] = None
    image: Optional[LLMMessageContentImage] = None

    def __repr__(self):
        if self.type == "text":
            return f"LLMMessageContent(type='text', text='{self.text}')"
        elif self.type == "image" and self.image:
            return f"LLMMessageContent(type='image', image={repr(self.image)})"
        return f"LLMMessageContent(type='{self.type}')"

    @classmethod
    def create_text_content(cls, text: str) -> "LLMMessageContent":
        return cls(type="text", text=text)

    @classmethod
    def create_image_url(cls, url: str) -> "LLMMessageContent":
        """URLより画像コンテンツを作成する"""
        return cls(type="image", image=LLMMessageContentImage(url=url))

    @classmethod
    def create_image_from_file(
        cls, file_path: str, mime_type: str = None
    ) -> "LLMMessageContent":
        """ファイルパスより画像コンテンツを作成する"""
        return cls(
            type="image",
            image=LLMMessageContentImage.create_content_image_from_file(
                file_path, mime_type
            ),
        )

    @classmethod
    def create_image_from_data(
        cls, data: bytes, mime_type: str = None, file_path: str = None
    ) -> "LLMMessageContent":
        """バイナリデータより画像コンテンツを作成する"""
        return cls(
            type="image",
            image=LLMMessageContentImage.create_content_image_from_data(
                data, mime_type, file_path
            ),
        )

    @classmethod
    def create_image(
        cls, url: str = None, base64_data: str = None, mime_type: str = None
    ) -> "LLMMessageContent":
        """画像コンテンツを作成する"""
        return cls(
            type="image",
            image=LLMMessageContentImage(
                url=url, base64_data=base64_data, mime_type=mime_type
            ),
        )

    def to_dict(self) -> dict:
        data = {
            "type": self.type,
            "text": self.text,
            "image": self.image.to_dict() if self.image else None,
        }
        return {k: v for k, v in data.items() if v is not None}

    def to_format_type(self, llm_type=LLMClientType.OPENAI.value) -> dict:
        if (
            llm_type == LLMClientType.OPENAI.value
            or llm_type == LLMClientType.OPENROUTER.value
        ):
            # OpenAIおよびOpenRouter形式
            if self.type == "text":
                return {"type": "text", "text": self.text}
            elif self.type == "image":
                image_data = self.image.to_dict()
                if not image_data.get("url") and not image_data.get("base64_data"):
                    raise ValueError(
                        "Image URL or base64 is required for OpenAI format."
                    )

                if image_data.get("base64_data"):
                    return {
                        "type": "image_url",
                        "image_url": {"url": self.image.base64_data_url()},
                    }
                else:
                    return {
                        "type": "image_url",
                        "image_url": {"url": image_data["url"]},
                    }
            else:
                raise ValueError(
                    f"Unsupported content type '{self.type}' for OpenAI format."
                )
        elif llm_type == LLMClientType.ANTHROPIC.value:
            if self.type == "text":
                return {"type": "text", "text": self.text}
            elif self.type == "image":
                image_data = self.image.to_dict()
                if not image_data.get("url") and not image_data.get("base64_data"):
                    raise ValueError(
                        "Image URL or base64 is required for OpenAI format."
                    )
                if image_data.get("base64_data"):
                    return {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image_data.get("mime_type"),
                            "data": image_data["base64_data"],
                        },
                    }
                else:
                    return {
                        "type": "image",
                        "source": {"type": "url", "url": image_data["url"]},
                    }
            else:
                raise ValueError(
                    f"Unsupported content type '{self.type}' for Anthropic format."
                )
        elif llm_type == LLMClientType.GEMINI.value:
            if self.type == "text":
                return {"text": self.text}
            elif self.type == "image":
                image_data = self.image.to_dict()
                if not image_data.get("url") and not image_data.get("base64_data"):
                    raise ValueError(
                        "Image URL or base64 is required for OpenAI format."
                    )
                if image_data.get("base64_data"):
                    return {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_data["base64_data"],
                        }
                    }
                else:
                    return {
                        "file_data": {
                            "mime_type": "image/jpeg",
                            "file_uri": image_data["url"],
                        }
                    }
            else:
                raise ValueError(
                    f"Unsupported content type '{self.type}' for Gemini format."
                )

    @classmethod
    def from_dict(cls, data: dict) -> "LLMMessageContent":
        image = data.get("image")
        if image and isinstance(image, dict):
            image = LLMMessageContentImage(**image)

        return cls(type=data["type"], text=data.get("text"), image=image)


# 型エイリアスの定義(ファイル上部などでまとめて)
MessageContentType = Union[str, List["LLMMessageContent"]]


@dataclass
class LLMMessage:
    """
    LLMMessageクラスは、LLM(大規模言語モデル)からのメッセージを表します。
    このクラスは、LLMからのレスポンスを格納するためのデータ構造を提供します。
    """

    role: LLMMessageRole
    content: Optional[MessageContentType] = None
    tool_calls: Optional[List[LLMMessageTool]] = None
    tool_call_id: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None

    @classmethod
    def create_user_message(
        cls,
        content: MessageContentType,
        meta_data: Optional[Dict[str, Any]] = None,
    ) -> "LLMMessage":
        """ユーザーからのメッセージを作成する"""
        return cls(role=LLMMessageRole.USER, content=content, meta_data=meta_data)

    @classmethod
    def create_assistant_message(cls, content: MessageContentType) -> "LLMMessage":
        """LLMからのメッセージを作成する"""
        return cls(role=LLMMessageRole.ASSISTANT, content=content)

    @classmethod
    def create_tools_call(cls, tools: List[LLMMessageTool]) -> "LLMMessage":
        """LLMからツールの呼び出しを受け取った場合のメッセージを作成する"""
        return cls(role=LLMMessageRole.ASSISTANT, tool_calls=tools)

    @classmethod
    def create_tools_result(cls, tool_call_id: str, content: str) -> "LLMMessage":
        """LLMからツールの呼び出し事項した結果のメッセージを作成する"""
        return cls(
            role=LLMMessageRole.TOOL,
            tool_call_id=tool_call_id,
            content=content,
        )

    @classmethod
    def create_meta_data(
        cls,
        key: str,
        meta_data: Dict[str, Any],
        role: LLMMessageRole = LLMMessageRole.ASSISTANT,
    ) -> "LLMMessage":
        """メタ情報のみのメッセージを作成する"""
        return cls(
            role=role,
            meta_data={key: meta_data},
        )

    def to_dict(self) -> Dict[str, Any]:
        """メッセージを辞書形式に変換する"""

        def convert(obj):
            if isinstance(obj, list):
                return [convert(o) for o in obj]
            elif hasattr(obj, "to_dict"):
                return obj.to_dict()
            else:
                return obj

        data = {
            "role": self.role.value,
            "content": convert(self.content),
            "tool_calls": convert(self.tool_calls),
            "tool_call_id": self.tool_call_id,
            "meta_data": convert(self.meta_data),
        }
        return {k: v for k, v in data.items() if v is not None}

    def to_format_type(self, llm_type=LLMClientType.OPENAI.value) -> dict:
        if self.meta_data:
            if self.meta_data.get("openai_stream_meta"):
                return self.meta_data.get("openai_stream_meta")

        data = {}
        data["role"] = self.role.format(llm_type)
        if self.content is not None and self.tool_call_id is None:
            if not llm_type == LLMClientType.GEMINI.value:
                if isinstance(self.content, str):
                    data["content"] = self.content
                else:
                    # Handle both LLMMessageContent and Response types
                    formatted_content = []
                    for c in self.content:
                        formatted_content.append(c.to_format_type(llm_type))
                    data["content"] = formatted_content
            else:
                # Geminiの形式
                if isinstance(self.content, str):
                    data["parts"] = [{"text": self.content}]
                else:
                    formatted_parts = []
                    for c in self.content:
                        formatted_parts.append(c.to_format_type(llm_type))
                    data["parts"] = formatted_parts
        if self.tool_calls is not None:
            if llm_type == LLMClientType.OPENAI.value:
                data["tool_calls"] = [
                    tool.to_format_type(llm_type) for tool in self.tool_calls
                ]
            elif llm_type == LLMClientType.ANTHROPIC.value:
                data["content"] = [
                    tool.to_format_type(llm_type) for tool in self.tool_calls
                ]
            elif llm_type == LLMClientType.GEMINI.value:
                data["parts"] = [
                    tool.to_format_type(llm_type) for tool in self.tool_calls
                ]
        if self.tool_call_id is not None:
            if llm_type == LLMClientType.OPENAI.value:
                data["content"] = self.content
                data["tool_call_id"] = self.tool_call_id
            elif llm_type == LLMClientType.ANTHROPIC.value:
                data["content"] = [
                    {
                        "type": "tool_result",
                        "tool_use_id": self.tool_call_id,
                        "content": self.content,
                    }
                ]
            elif llm_type == LLMClientType.GEMINI.value:
                data["parts"] = [
                    {
                        "functionResponse": {
                            "name": self.tool_call_id,
                            "response": {"result": self.content},
                        }
                    }
                ]
        return {k: v for k, v in data.items() if v is not None}

    @staticmethod
    def to_dict_messages(messages: List["LLMMessage"]) -> List[Dict[str, str]]:
        return [msg.to_dict() for msg in messages]

    @staticmethod
    def to_format_messages(
        messages: List["LLMMessage"], llm_type=LLMClientType.OPENAI.value
    ) -> List[Dict[str, str]]:
        return [msg.to_format_type(llm_type) for msg in messages]

    @classmethod
    def from_dict_messages(cls, messages_dic: List[dict]) -> List["LLMMessage"]:
        result = []
        for item in messages_dic:
            role = LLMMessageRole(item["role"])  # Enum化

            content = item.get("content")
            if content is not None:
                if isinstance(content, list):
                    content = [LLMMessageContent.from_dict(c) for c in content]

            tool_calls_data = item.get("tool_calls")
            tool_calls = None
            if tool_calls_data:
                tool_calls = [LLMMessageTool.from_dict(tc) for tc in tool_calls_data]

            tool_call_id = item.get("tool_call_id")

            result.append(
                cls(
                    role=role,
                    content=content,
                    tool_calls=tool_calls,
                    tool_call_id=tool_call_id,
                )
            )
        return result
