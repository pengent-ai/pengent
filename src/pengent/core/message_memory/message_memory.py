from typing import Optional, List, Union
from ...type.llm.llm_message import (
    LLMMessage,
    LLMMessageRole,
    LLMMessageTool,
    MessageContentType,
)


class MessageMemoryBase:
    """
    メッセージ管理をおこなう

    Functions:
        add(): role/content などを直接渡すシンプルAPI
        add_message(): LLMMessage を直接渡す詳細API
    """

    def __init__(self, max_messages: int = 30, _type: Optional[str] = None):
        self.max_messages = max_messages
        self.messages: list[LLMMessage] = []
        self._type = _type

    def _add_message(self, message: LLMMessage):
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def add(
        self,
        role: Union[str, LLMMessageRole],
        content: Optional[MessageContentType] = None,
        tool_calls: Optional[List[LLMMessageTool]] = None,
        tool_call_id: Optional[str] = None,
    ):
        # 文字列を Enum に変換
        if isinstance(role, str):
            role = LLMMessageRole(role)

        self._add_message(
            LLMMessage(
                role=role,
                content=content,
                tool_calls=tool_calls,
                tool_call_id=tool_call_id,
            )
        )

    def add_message(self, message: LLMMessage):
        """メッセージを追加する(メッセージ型)"""
        self._add_message(message)

    def clear(self):
        """メッセージをクリアする"""
        self.messages.clear()

    def get(self):
        return self.messages

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"<MessageMemoryBase messages={self.to_dict()}>"

    def to_dict(self) -> dict:
        return {
            "max_messages": self.max_messages,
            "type": self._type,
            "messages": LLMMessage.to_dict_messages(self.messages),
        }

    @classmethod
    def from_dict(cls, dic_data: dict) -> "MessageMemoryBase":
        cls_obj = cls(
            max_messages=dic_data.get("max_messages", 30),
            _type=dic_data.get("type", None),
        )
        cls_obj.messages = LLMMessage.from_dict_messages(dic_data.get("messages", []))
        return cls_obj
