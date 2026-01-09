import numpy as np
from uuid import uuid4

from typing import List, Optional, Union
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams, ScoredPoint
from .vectore_store_interface import VectorStoreInterface


class QdrantStore(VectorStoreInterface):
    """

    Notes:
        `pip install qdrant-client`
    """

    def __init__(self, dim: int, config: Optional[dict] = None):
        """
        QdrantStoreの初期化

        Parameters:
            dim (int): ベクトルの次元数
        Notes:
            - Qdrantはベクトルストアのため、次元数は必須です。
            - dimは埋め込みモデルに合わせる必要があります。
        """

        if config is None:
            config = {
                "host": "localhost",
                "port": 6333,
                "collection_name": "rag_collection",
                # "distance": "Cosine"  # または "Euclid", "Dot"
            }
        super().__init__(config=config)
        self.client = QdrantClient(
            url=config.get("url") or f"http://{config['host']}:{config['port']}"
        )
        self.collection_name = config["collection_name"]

        # コレクションが存在しない場合は作成
        if not self.client.collection_exists(self.collection_name):
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=dim,
                    distance=Distance.COSINE,
                    # [config.get("distance", "Cosine")]
                ),
            )

    def add(self, metadata: dict, vector: Union[List[float], np.ndarray]):
        """
        ベクトルとメタデータを追加
        """
        if isinstance(vector, np.ndarray):
            if vector.ndim == 1:
                vector = vector.tolist()
            elif vector.ndim == 2:
                vector = vector[0].tolist()
            else:
                raise ValueError("Unsupported array shape")

        point = PointStruct(
            id=metadata.get("id", str(uuid4())), vector=vector, payload=metadata
        )
        self.client.upsert(collection_name=self.collection_name, points=[point])

    def search(
        self, query_vector: Union[List[float], np.ndarray], top_k: int
    ) -> List[dict]:
        """
        類似ベクトルを検索
        """
        if isinstance(query_vector, np.ndarray):
            if query_vector.ndim == 1:
                query_vector = query_vector.tolist()
            elif query_vector.ndim == 2:
                query_vector = query_vector[0].tolist()
            else:
                raise ValueError("Unsupported array shape")

        results: List[ScoredPoint] = self.client.search(
            collection_name=self.collection_name, query_vector=query_vector, limit=top_k
        )
        return [point.payload for point in results]

    def save(self, *args, **kwargs):
        """
        Qdrantはサーバー内で永続化されているため明示的な保存は不要
        """
        self.logger.info("Qdrant は自動的に永続化されます。save() は不要です。")

    def load(self, *args, **kwargs):
        """
        Qdrantは自動的に永続化されているため明示的なロードは不要
        """
        self.logger.info("Qdrant は自動的に永続化されます。load() は不要です。")
