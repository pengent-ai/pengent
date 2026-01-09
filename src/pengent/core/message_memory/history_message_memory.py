from typing import Optional
from .message_memory import MessageMemoryBase
from .storage.memory_storage_interface import MemoryStorageInterface


class HistoryMessageMemory(MessageMemoryBase):
    """
    メモリの履歴を保持するクラス
    """

    def __init__(
        self,
        max_messages: int = 50,
        storage: Optional[MemoryStorageInterface] = None,
    ):
        super().__init__(max_messages, _type="history")
        self.storage = storage

    def save(self):
        if self.storage:
            self.storage.save(self.to_dict())
        else:
            raise ValueError("Storage is not set.")

    def load(self):
        if self.storage:
            dates = self.storage.load()  # List[dict] が返る想定
            self.messages = self.from_dict(dates)
        else:
            raise ValueError("Storage is not set.")
