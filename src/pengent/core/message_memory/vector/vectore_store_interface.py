from abc import ABC, abstractmethod
from typing import List, Optional
from ....lib.custom_logger import get_logger


class VectorStoreInterface(ABC):
    """
    ベクトルストアのインターフェースクラス
    """
    def __init__(self, config: Optional[dict] = None):
        """
        ベクトルストアのインターフェースクラス
        """
        self.config = config if config is not None else {}
        self.logger = get_logger()

    @abstractmethod
    def add(self, metadata: dict, vector: List[float]): ...

    @abstractmethod
    def search(self, query_vector: List[float], top_k: int) -> List[dict]: ...
