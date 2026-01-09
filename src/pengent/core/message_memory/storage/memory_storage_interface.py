from abc import ABC, abstractmethod
from typing import List


class MemoryStorageInterface(ABC):
    """メモリストレージの共通インターフェース"""

    @abstractmethod
    def save(self, messages: List[dict]) -> None:
        pass

    @abstractmethod
    def load(self) -> List[dict]:
        pass
