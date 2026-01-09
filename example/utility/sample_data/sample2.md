# 検索拡張生成(RAG)の完全ガイド

RAG(Retrieval-Augmented Generation)は、生成AIと情報検索の融合技術です。大規模言語モデル(LLM)に対して、外部知識を与えることで、より正確で信頼性の高い出力を実現します。

---

## RAGとは？

RAGは以下の2つの主なステップから成り立ちます：

1. **Retriever(検索)**: クエリに基づいて関連情報を検索
2. **Generator(生成)**: 検索結果を参考にしてテキストを生成

この手法により、モデルが学習していない事実や最新情報を生成結果に反映できます。

---

## ベクトルデータベースの比較

| データベース | 特徴 | 言語対応 | ストレージ形式 |
|--------------|------|----------|----------------|
| Qdrant        | REST/GRPC対応。タグ検索が強力 | 多言語対応 | Disk + RAM |
| FAISS         | 高速・軽量だがメタデータに弱い | 英語中心 | RAM中心 |
| Weaviate      | GraphQL対応、スキーマあり | 英語＋多言語 | 分散可 |
| Chroma        | Python向けで手軽 | 多言語対応 | ローカルに最適 |

---

## コード例：OpenAI埋め込みを使ったQdrant登録

```python
from qdrant_client import QdrantClient
from openai import OpenAIEmbeddings

embedder = OpenAIEmbeddings()
vector = embedder.embed("これはサンプルの文です。")
client = QdrantClient(host="localhost", port=6333)
client.upsert(
    collection_name="rag",
    points=[{"id": "doc1", "vector": vector, "payload": {"text": "これはサンプル"}}]
)
```

---

## よくある質問(FAQ)

### Q: ベクトルの次元数は揃える必要がありますか？

はい。同一コレクション内ではすべてのベクトルが同じ次元数である必要があります。

### Q: 日本語にはどの埋め込みモデルがおすすめですか？

[`bge-base-ja`](https://huggingface.co/embedding-data/bge-base-ja) など、特に日本語向けに調整されたモデルが効果的です。

---

## 参考リンク

* [Qdrant公式ドキュメント](https://qdrant.tech/documentation/)
* [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
* [RAG論文(original paper)](https://arxiv.org/abs/2005.11401)

