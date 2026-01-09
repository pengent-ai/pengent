# FAQ Analyzer

`pengent.utility.faq_analyzer`は、ウェブページやドキュメントからFAQペアを自動抽出し、RAG(Retrieval-Augmented Generation)システムで利用可能な形に処理するPythonライブラリです。

## 主な機能

- **FAQ自動抽出**: ウェブページからQ&A形式のコンテンツを自動的に抽出
- **構造化処理**: SimpleFAQRagFormatでの統一された形式での処理
- **ベクトル検索**: ベクトル化とFaissStoreを使用した高速な類似度検索
- **カスタマイズ可能**: 抽出ルールや検索設定を詳細にカスタマイズ
- **統計情報**: 処理したFAQデータの統計情報を提供

## クイックスタート

### 基本的な使用方法

```python
from pengent.utility.faq_analyzer import FAQAnalyzer

# FAQAnalyzerの初期化
analyzer = FAQAnalyzer()

# URLからFAQ抽出〜ベクトルストア構築まで一括処理
url = "https://example.com/faq"
faq_pairs, vector_store = analyzer.process_url_complete(url)

print(f"抽出されたFAQ数: {len(faq_pairs)}")

# 検索
results = analyzer.search("使い方について", top_k=3)
for result in results:
    print(f"Q: {result['question']}")
    print(f"A: {result['answer'][:100]}...")
```

### 手動でFAQを追加

```python
analyzer = FAQAnalyzer()

# 手動でFAQペアを追加
analyzer.add_manual_faq(
    question="FAQAnalyzerとは何ですか？",
    answer="ウェブページからFAQを抽出してRAG処理するライブラリです。",
    tags=["基本概念", "ライブラリ"]
)

# ベクトルストア構築
vector_store = analyzer.build_vector_store()

# 検索
results = analyzer.search("FAQAnalyzerについて")
```

## カスタム設定

### 設定オプション

```python
from pengent.utility.faq_analyzer import FAQAnalyzer, FAQAnalysisConfig

# カスタム設定
config = FAQAnalysisConfig(
    include_tags=["h1", "h2", "h3", "p", "li"],  # 解析対象のHTMLタグ
    question_indicators=["Q:", "質問", "？"],      # 質問を示すキーワード
    min_answer_length=20,                         # 回答の最小文字数
    max_answer_length=1000,                       # 回答の最大文字数
    similarity_threshold=0.7                      # 検索結果の類似度閾値
)

analyzer = FAQAnalyzer(config=config)
```

### エンベッダーのカスタマイズ

```python
from pengent.utility.embed.embed_with_local import LocalEmbedder

# カスタムエンベッダー
embedder = LocalEmbedder()
analyzer = FAQAnalyzer(embedder=embedder)
```

## 詳細な使用例

### ステップバイステップ処理

```python
analyzer = FAQAnalyzer()

# 1. URLからFAQペア抽出
faq_pairs = analyzer.extract_faq_pairs_from_url(url)

# 2. SimpleFAQRagFormat処理
faq_documents = analyzer.process_faq_pairs(faq_pairs)

# 3. ベクトルストア構築
vector_store = analyzer.build_vector_store(faq_documents)

# 4. 検索
results = analyzer.search("検索クエリ", top_k=5)
```

### ブロックデータからの直接抽出

```python
# 既に解析済みのブロックデータから抽出
blocks = [
    {"type": "heading", "content": "Q: 質問文", "level": 2},
    {"type": "paragraph", "content": "A: 回答文"}
]

faq_pairs = analyzer.extract_faq_pairs_from_blocks(blocks, "source_url")
```

## 統計情報とエクスポート

### 統計情報の取得

```python
stats = analyzer.get_faq_statistics()
print(f"総FAQ数: {stats['total_faqs']}")
print(f"平均質問長: {stats['avg_question_length']:.1f}")
print(f"平均回答長: {stats['avg_answer_length']:.1f}")
print(f"主要タグ: {stats['common_tags']}")
```

### データのエクスポート

```python
# JSON形式でエクスポート
exported_data = analyzer.export_faqs("json")
print(f"エクスポート完了: {len(exported_data)}件のFAQ")
```

## 検索機能

### 基本的な検索

```python
# 類似度検索
results = analyzer.search("エラーの対処法", top_k=5)

for result in results:
    print(f"質問: {result['question']}")
    print(f"回答: {result['answer']}")
    print(f"タグ: {', '.join(result['tags'])}")
    print(f"スコア: {result['score']:.4f}")
    print("---")
```

### 高度な検索

```python
# 閾値を指定した検索(configで設定済みの閾値を使用)
results = analyzer.search("技術的な問題", top_k=10)

# 関連するFAQのみを取得
relevant_results = [r for r in results if r.get('score', 0) > 0.8]
```

## データクラス

### FAQPair

```python
from pengent.utility.faq_analyzer import FAQPair

faq = FAQPair(
    question="質問文",
    answer="回答文",
    source_url="https://example.com",
    confidence=1.0,
    tags=["タグ1", "タグ2"]
)
```

### FAQAnalysisConfig

設定可能なパラメータ：

- `include_tags`: 解析対象のHTMLタグのリスト
- `exclude_tags`: 除外するHTMLタグのリスト
- `question_indicators`: 質問を示すキーワードのリスト
- `answer_indicators`: 回答を示すキーワードのリスト
- `min_answer_length`: 回答の最小文字数
- `max_answer_length`: 回答の最大文字数
- `vector_dim`: ベクトルの次元数(オプション)
- `similarity_threshold`: 検索結果の類似度閾値

## エラーハンドリング

```python
try:
    faq_pairs, vector_store = analyzer.process_url_complete(url)
except Exception as e:
    print(f"FAQ抽出に失敗: {str(e)}")
    # サンプルデータやフォールバック処理
```

## パフォーマンス最適化

### バッチ処理

```python
# 複数URLの一括処理
urls = ["url1", "url2", "url3"]
all_faq_pairs = []

for url in urls:
    try:
        faq_pairs = analyzer.extract_faq_pairs_from_url(url)
        all_faq_pairs.extend(faq_pairs)
    except Exception as e:
        print(f"URL {url} の処理に失敗: {e}")

# 一括でベクトルストア構築
faq_documents = analyzer.process_faq_pairs(all_faq_pairs)
vector_store = analyzer.build_vector_store(faq_documents)
```

### メモリ管理

```python
# データクリア
analyzer.clear()  # すべてのFAQデータとベクトルストアをクリア
```

## 実践例

完全な使用例は `example/utility/example_faq_analyzer.py` を参照してください。

```bash
# 使用例の実行
python example/utility/example_faq_analyzer.py
```

## 依存関係

- `pengent.tools.api.search.page.api_webpage`: ウェブページ解析
- `pengent.utility.embed.embed_with_local`: ローカルエンベッダー
- `pengent.core.message_memory.vector.faissy_store`: ベクトルストア
- `pengent.type.rag.SimpleFAQRagFormat`: FAQ RAGフォーマット

## トラブルシューティング

### よくある問題

1. **URLアクセスエラー**: ネットワーク接続やURL形式を確認
2. **FAQ抽出数が少ない**: `question_indicators`や`include_tags`の設定を調整
3. **検索結果が見つからない**: `similarity_threshold`を下げて試行
4. **メモリ不足**: 大量データ処理時は`clear()`でメモリを解放

### デバッグ

```python
import logging
logging.basicConfig(level=logging.INFO)

# ログ出力でデバッグ情報を確認
analyzer = FAQAnalyzer()
``` 