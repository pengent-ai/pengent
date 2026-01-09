## Slack(WebHook)で受信後にメッセージを送信すると同じメッセージが3回送信される

**環境構成**:
* FastAPI
* Croud Run(ホットスタンバイ) 


Slackは **Webhookの応答が3秒以内にないと「失敗」とみなして再送**してくるため
「同じイベントが複数回送られる」状況になっていると思われる

### 原因まとめ

| 項目        | 内容                                                                             |
| ----------- | -------------------------------------------------------------------------------- |
| Slackの仕様 | 3秒以内に200 OKを返さないと、**最大3回まで再送**                                 |
| Cloud Run   | インスタンスがゼロから起動する場合(コールドスタート)に**数秒かかる**ことがある |
| 結果        | Slackが「失敗」と判断 → **同じイベントを何度も送ってくる**                       |

### 解決策・対策一覧

#### **即時レスポンス + 非同期処理**

Slackにはすぐに200 OKを返しておいて、実処理はバックグラウンドで実行する方式が最適です。

```python
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/webhooks/slack")
async def slack_webhook(payload: dict, background_tasks: BackgroundTasks):
    event_id = payload.get("event_id")

    # 重複チェックを行う場合はここで
    if is_duplicate(event_id):
        return JSONResponse({"status": "duplicate"})

    # 即レスポンスしつつ非同期で処理を実行
    background_tasks.add_task(process_slack_event, payload)
    return JSONResponse({"status": "ok"})  # ← Slackに即時OK
```

#### **イベントIDで重複防止**

Slackの各イベントには `event_id` があります。
これを**一時的にキャッシュ(例：Redis)** しておけば重複防止に使えます。

redisを利用する場合

```python
def is_duplicate(event_id):
    if redis.exists(event_id):
        return True
    redis.set(event_id, "1", ex=300)  # 5分間保持
    return False
```

---

### 対応まとめ

| 対策                     | 説明                               |
| ------------------------ | ---------------------------------- |
| 即時200 OKを返す         | Slackの再送防止(非同期処理)      |
| 最小インスタンス数を設定 | コールドスタート対策(コスト増加) |
| `event_id` で重複防止    | Slackの再送に対抗する基本戦略      |

---

必要であれば、非同期処理の設計やRedisを使った重複検出コードも具体的に提示できます！

### その他の対応

FIFO

```py
from collections import deque

class SlackBotServer:
    def __init__(self):
        # 最大10件のevent_idを保持
        self.recent_event_ids = deque(maxlen=10)

    def is_duplicate(self, event_id: str) -> bool:
        if event_id in self.recent_event_ids:
            return True
        self.recent_event_ids.append(event_id)
        return False
```

時間付きキャッシュ

```py
import time

class SlackBotServer:
    def __init__(self):
        self.event_cache = {}  # {event_id: timestamp}

    def is_duplicate(self, event_id: str, ttl: int = 300) -> bool:
        now = time.time()
        # 過去のevent_idをTTLに基づいて削除
        self.event_cache = {
            k: v for k, v in self.event_cache.items()
            if now - v < ttl
        }
        if event_id in self.event_cache:
            return True
        self.event_cache[event_id] = now
        return False
```