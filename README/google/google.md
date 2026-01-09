## 事前準備(Google Cloud Console)

1. Google Cloud Consoleにアクセス
2. プロジェクト作成(または既存プロジェクト選択)
3. 「APIとサービス」→「認証情報」へ移動
4. 「OAuth 2.0 クライアントID」を作成(アプリケーションの種類: デスクトップアプリなど)
5. client_id.json をダウンロード

```sh
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

