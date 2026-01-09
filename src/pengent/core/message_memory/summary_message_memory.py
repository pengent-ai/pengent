from typing import Optional, Callable, List
from .message_memory import MessageMemoryBase
from ...llm import LLMClientBase
from ...type.llm.llm_message import LLMMessage
from ...utility.summarize import summarize


class SummaryMessageMemory(MessageMemoryBase):
    """要約メッセージメモリクラス"""

    def __init__(
        self,
        summarizer: Optional[
            Callable[[List[LLMMessage], Optional[LLMClientBase]], str]
        ] = None,
        max_messages=10,
    ):
        """
        要約メモリの初期化

        Params:
            summarizer: 要約を行うLLMなどのインスタンス
            max_messages: メモリに保持するメッセージの最大数
        """
        super().__init__(max_messages, _type="summary")
        if summarizer is None:
            summarizer = summarize

        self.summarizer = summarizer
        self.summary = ""

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        if len(self.messages) >= self.max_messages:
            self._summarize()

    def _summarize(self):
        self.summary += "\n" + self.summarizer(self.messages)
        self.messages = []

    def get(self) -> list:
        return [{"role": "system", "content": self.summary}] + self.messages
