import json
from typing import List
from .memory_storage_interface import MemoryStorageInterface


class FileMemoryStorage(MemoryStorageInterface):
    """
    ファイルベースのメモリストレージ実装クラス
    """
    def __init__(self, path: str):
        self.path = path

    def save(self, messages: List[dict]) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)

    def load(self) -> List[dict]:
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)
