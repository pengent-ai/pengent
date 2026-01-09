import os
from typing import List, Union
from openai import OpenAI
import numpy as np
from .embed_base import EmbedderBase


class OpenAIEmbedder(EmbedderBase):
    """
    OpenAIのtext-embeddingモデルを使用してベクトル化を行うクラス。

    Notes:
        - デフォルトで "text-embedding-3-small" を使用
        - OPENAI_API_KEY 環境変数 または api_key パラメータのどちらかが必要
    """

    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.model_name = model_name
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)

    def encode(
        self, texts: Union[str, List[str]], to_numpy: bool = False
    ) -> Union[List[float], List[List[float]]]:
        if isinstance(texts, str):
            texts = [texts]

        response = self.client.embeddings.create(model=self.model_name, input=texts)

        vectors = [item.embedding for item in response.data]

        if to_numpy:
            return np.array(vectors, dtype=np.float32)

        return vectors[0] if len(vectors) == 1 else vectors
