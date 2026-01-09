from .faissy_store import FaissStore
from .qdrant_store import QdrantStore
from ....utility.embed.embed_with_local import LocalEmbedder
from ....utility.embed.embed_with_openai import OpenAIEmbedder

# モデル名に対する次元数のマッピング
EMBEDDING_MODEL_DIMS = {
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 384,
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    # 必要に応じて追加
}
DEFAULT_DIM = 384  # モデル指定なしの場合のデフォルト


def get_vector_store(store_type: str, config: dict, model_name: str = None):
    if model_name is None:
        model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    dim = EMBEDDING_MODEL_DIMS.get(model_name, DEFAULT_DIM)
    if store_type == "qdrant":
        return QdrantStore(dim=dim, config=config)
    elif store_type == "faiss":
        return FaissStore(dim=dim, config=config)
    elif store_type == "chroma":
        raise NotImplementedError("Chroma対応は未実装です")
    else:
        raise ValueError(f"Invalid vector store type: {store_type}")


def get_vector_store_and_embedder(
    store_type: str, config: dict, model_name: str = None
):
    if model_name is None:
        model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    dim = EMBEDDING_MODEL_DIMS.get(model_name, DEFAULT_DIM)
    if store_type == "qdrant":
        store = QdrantStore(dim=dim, config=config)
    elif store_type == "faiss":
        store = FaissStore(dim=dim, config=config)
    elif store_type == "chroma":
        raise NotImplementedError("Chroma対応は未実装です")
    else:
        raise ValueError(f"Invalid vector store type: {store_type}")

    if model_name.startswith("text-embedding"):
        embedder = OpenAIEmbedder(model_name=model_name)
    elif model_name.startswith("sentence-transformers/"):
        embedder = LocalEmbedder(model_name=model_name)
    else:
        raise ValueError(f"Unsupported model name: {model_name}")

    return store, embedder


def search(
    query_text: str,
    store_type: str,
    config: dict,
    model_name: str = None,
    top_k: int = 3,
):
    store, embedder = get_vector_store_and_embedder(
        store_type, config, model_name=model_name
    )
    query_vector = embedder.encode(query_text, to_numpy=True)
    results = store.search(query_vector, top_k=top_k)
    return results
