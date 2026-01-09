import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
)

from pengent.lib import get_logger

logger = get_logger(level=10)

from dotenv import load_dotenv

load_dotenv()

from pengent.tools.api.post.api_qiita import ApiQiita, ApiQiitaTag


def example_create_post():
    title = (
        "[Docker][構築ファイル] Node.js(フロントエンド)と"
        "Python(バックエンド)を1つのDockerコンテナにまとめたい"
    )
    tags = [
        ApiQiitaTag(name="Docker"),
        ApiQiitaTag(name="Python", versions=["3.11"]),
        ApiQiitaTag(name="Node.js"),
        ApiQiitaTag(name="フルスタック"),
        ApiQiitaTag(name="Web開発"),
    ]

    content = """# [Docker][構築ファイル] Node.js(フロントエンド)と Python(バックエンド)を 1 つの Docker コンテナにまとめたい

## はじめに

開発時などに、Node.js(フロント)と Python(バックエンド)を同じ Docker コンテナ内でまとめて動かしたいことがあります。
この記事では、`python:3.11-slim` ベースの軽量イメージを用い、1 つの Docker コンテナ内で Node.js + Python を構築・起動する方法を解説します。

---

## Dockerfile のサンプル

```dockerfile
FROM python:3.11-slim

# Node.js を追加
RUN apt-get update && apt-get install -y curl gnupg \\
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \\
    && apt-get install -y nodejs \\
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ
WORKDIR /app

# Python & Node.js の依存ファイルをコピー
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY package.json .
RUN npm install

# アプリ全体をコピー
COPY . .

# start.sh に実行権限を付与
RUN chmod +x start.sh

# 起動コマンド
CMD ["./start.sh"]
````

---

## 2 つのサーバーを実行する方法(フロント + バックエンド)

### 方法1: シェルファイルで 2 プロセス同時起動

まず `start.sh` ファイルを作成します：

```sh
#!/bin/bash

# フロントエンドをバックグラウンドで起動
cd frontend
npm run start &

# 少し待ってから(任意)
sleep 2

# バックエンドを起動
cd ..
python main.py
```

このスクリプトにより、Node.js(例: Vite, Next.js)と Python の両方を同時に起動できます。

---

### 方法2: Python コードからフロントを起動する

Python の `subprocess` を使って Node.js をバックグラウンド起動することで、1 ファイルで管理できます。

```python
import subprocess
import time
from fastapi import FastAPI

# Node.js フロントエンドをバックグラウンドで起動
subprocess.Popen(["npm", "run", "start"], cwd="./frontend")

# 少し待機してバックエンド起動(任意)
time.sleep(2)

# FastAPI サーバー起動(例)
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from backend"}
```

この方法では、スレッドを使わずにノンブロッキングに起動可能です。

---

## TL;DR

* `subprocess.Popen(...)` は非同期(ノンブロッキング)でプロセスを起動できます。
* **エラー処理やログ監視が不要であれば、`threading.Thread(...)` は基本不要です。**
* 最小構成であれば、以下のコードだけでも起動可能：

```python
subprocess.Popen(["npm", "run", "start"], cwd="./frontend")
```

---

## まとめ

開発環境であれば、Node.js と Python を 1 つの Docker コンテナでまとめて起動することは現実的かつ便利です。
ただし本番環境では、コンテナを分離して Docker Compose などで連携する構成が推奨されます。
"""  # noqa: E501

    # 投稿呼び出し(プライベート投稿、下書き状態)
    ApiQiita.post(
        title=title,
        content=content,
        tags=tags,
        private=False,
        coediting=False,
        gist=False,
        tweet=False,
    )


def example_get_posts():
    api = ApiQiita()
    res = api.get_posts(tag_query="Python", stocks_over=100)
    for article in res:
        logger.info(
            f"Title: {article['title']},likes_count: {article['likes_count']} "
            f"URL: {article['url']}"
        )
        logger.info(f"created_at: {article['created_at']}")


def example_get_tags():
    api = ApiQiita()
    res = api.get_tags()
    for tag in res:
        logger.info(f"{tag}")


def example_get_trand_tags():
    api = ApiQiita()
    res = api.get_trend_tags(page=1, per_page=50, stocks_over=100)
    for tag, count in res:
        logger.info(f"Tag: {tag}, Count: {count}")


def example_create_post_file():
    # ファイルからMarkdown記事の内容を読み込む
    with open("output.txt", "r", encoding="utf-8") as f:
        content = f.read()

    title = (
        "VSCodeで画像に簡単に赤マーク！手順書が爆速に。"
        "AI×人間で半日開発した「ImageMarkPengent」"
    )
    
    tags = [
        ApiQiitaTag(name="VSCode"),
        ApiQiitaTag(name="画像加工"),
        ApiQiitaTag(name="開発ツール"),
        ApiQiitaTag(name="AI活用事例"),
        ApiQiitaTag(name="OSS"),
    ]

    # 投稿呼び出し(プライベート投稿)
    ApiQiita.post(
        title=title,
        content=content,
        tags=tags,
        private=False,  # 最初はプライベート推奨
        coediting=False,
        gist=False,
        tweet=False,
    )


# example_get_trand_tags()
example_create_post_file()
