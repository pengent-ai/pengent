# Batch処理について

* Batchで実行すると半額になる
* OpenAI社とAnthropic社のLLMが対応している

## デフォルトモデル (v1.2.3)

* OpenAI Batch: `gpt-6-luna`
* Anthropic Batch: `claude-haiku-4-5-20251001`


## 仕様

* OpenAI
  * バッチJOBリクエスト 
    * JSONLファイルを生成する
    * バッチレコードを生成する
    * JSONLにバッチレコードを書き込む
    * LLMクライアントでレコードを送信する(ファイルをバイナリ送信する)
  * バッチJOBを確認する
    * LLMクライアントで状態を取得する
  * バッチIDのレスポンスを取得する
    * LLMクライアントでバッチIDの状態を取得する
    * 出力が存在し、バッチが完了していた場合
      * 対象IDの結果ファイルを取得する
      * ファイルのバイナリ情報を取得する
      * ファイルを出力する


```py
record = {
    "custom_id": custom_id if custom_id else str(uuid.uuid4()),
    "method": "POST",
    "url": "/v1/chat/completions",
    "body": {
        "model": self.model_name,
        "temperature": self.temperature,
        "messages": tmp_msg,
    }
}
```

## 処理

* LLMクライアント: APIを投げる

