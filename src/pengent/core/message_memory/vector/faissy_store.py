import faiss
from typing import List, Optional
import json
import numpy as np
import os

from .vectore_store_interface import VectorStoreInterface


class FaissStore(VectorStoreInterface):
    """
    Faissを用いたベクトルストアの実装クラス
    """
    def __init__(self, dim: int, config: Optional[dict] = None):
        """
        FaissStoreの初期化メソッド

        Parameters:
            dim (int): ベクトルの次元数(Faissのインデックス構築に必要)
        """
        self.index = faiss.IndexFlatL2(dim)
        self.vectors = []
        self.metadata = []
        if config is None:
            config = {
                "index_path": "rag_index.index",  # Faissのベクトルインデックスの保存先
                "docs_path": "rag_docs.json",  # メタデータの保存先
                "collection_name": "rag_collection",
                "auto_load": False,
                "auto_save": False,
            }
        super().__init__(config=config)
        if config.get("auto_load", False):
            self._auto_load()

    def add(self, metadata: dict, vector: List[float]):
        """
        ベクトルとメタデータを追加するメソッド

        Parameters:
            metadata (dict): ベクトルに関連するメタデータ
            vector (List[float]): ベクトルデータ
        """
        self.index.add(np.array([vector]).astype("float32"))
        self.vectors.append(vector)
        self.metadata.append(metadata)
        if self.config.get("auto_save", False):
            self.save()

    def search(self, query_vector: List[float], top_k: int):
        query_array = np.array(query_vector, dtype=np.float32)
        if query_array.ndim == 1:
            query_array = query_array.reshape(1, -1)
        D, indices = self.index.search(query_array, top_k)
        return [self.metadata[i] for i in indices[0]]

    def _auto_load(self):
        """
        自動的にインデックスとメタデータをロードする
        """
        index_path = self.config.get(
            "index_path", f"{self.config['collection_name']}.index"
        )
        docs_path = self.config.get(
            "docs_path", f"{self.config['collection_name']}.json"
        )

        if not index_path or not docs_path:
            raise ValueError("index_path または docs_path が指定されていません。")

        # ファイルが存在するか確認する
        if not os.path.exists(index_path) or not os.path.exists(docs_path):
            self.logger.info(
                "Index or docs file not found. "
                f"Creating new index and metadata at {index_path} and {docs_path}."
            )
            self.save()
        else:
            self.logger.info(
                f"Loading Faiss index and metadata from {index_path} and {docs_path}."
            )
            self.load()

    def save(self, index_path: Optional[str] = None, docs_path: Optional[str] = None):
        self.logger.debug("Saving Faiss index and metadata...")
        if not index_path:
            index_path = self.config.get(
                "index_path", f"{self.config['collection_name']}.index"
            )
        if not docs_path:
            docs_path = self.config.get(
                "docs_path", f"{self.config['collection_name']}.json"
            )
        if not index_path or not docs_path:
            raise ValueError("index_path または docs_path が指定されていません。")

        faiss.write_index(self.index, index_path)
        with open(docs_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        self.logger.debug(
            f"Saved {len(self.metadata)} vectors and metadata "
            f"to {index_path} and {docs_path}."
        )

    def load(self, index_path: Optional[str] = None, docs_path: Optional[str] = None):
        self.logger.debug("Loading Faiss index and metadata...")
        if not index_path:
            index_path = self.config.get(
                "index_path", f"{self.config['collection_name']}.index"
            )
        if not docs_path:
            docs_path = self.config.get(
                "docs_path", f"{self.config['collection_name']}.json"
            )
        if not index_path or not docs_path:
            raise ValueError("index_path または docs_path が指定されていません。")

        self.index = faiss.read_index(index_path)
        with open(docs_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
        self.logger.debug(
            f"Loaded {len(self.metadata)} vectors and metadata "
            f"from {index_path} and {docs_path}."
        )
