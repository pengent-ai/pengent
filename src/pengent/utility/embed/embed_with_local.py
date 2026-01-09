from sentence_transformers import SentenceTransformer
from typing import List, Union
from .embed_base import EmbedderBase

"""
- all-MiniLM-L6-v2
  - 軽量・高速・精度十分    ~80MB   英語中心 汎用RAG / FAQ検索 / 要約
  - 構文がシンプルな日本語ならそこそこ使える
- all-mpnet-base-v2
  - 精度重視・多言語対応    ~420MB  英語のみ 英語限定だが高精度
- paraphrase-multilingual-MiniLM-L12-v2
  - 多言語対応(日本語OK)  ~150MB  50+言語 日本語含むRAGやQ&A
- distiluse-base-multilingual
  - 多言語・精度重視        ~230MB	50+言語     RAGや感情分析など
"""


class LocalEmbedder(EmbedderBase):
    """
    テキストからベクトル化を行うクラス

    Notes:
        - SentenceTransformerを使用して、テキストをベクトル化します。
        - デフォルトでは、"paraphrase-multilingual-MiniLM-L12-v2"モデルを使用します。
        - 日本語にも対応しています。

    """

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.model = SentenceTransformer(model_name)

    def encode(
        self, texts: Union[str, List[str]], to_numpy: bool = False
    ) -> Union[List[float], List[List[float]]]:
        if isinstance(texts, str):
            texts = [texts]
        vectors = self.model.encode(texts, convert_to_numpy=to_numpy)
        return vectors[0] if len(texts) == 1 else vectors
