# penjent 🐧

**Pengent(ペンジェント)** は、軽量かつ汎用的な AIエージェントフレームワーク です。
ChatGPT・Claude・GeminiなどのLLMと、ツール実行やルール処理を組み合わせて、柔軟なマルチエージェント処理が行えます。

![pengent logo](README/images/log.png)

## Functions 

* 複数のLLMに対応：OpenAI / Claude / Gemini など、用途に応じて使い分け可能

## Usecase

* SlackやLINE BotなどチャットからAIで自動対応したい
* Faq用のエージェントをすぐに使いたい(RAGを活用すれば無料AIでも活用可能)

## Install

```
pip install git+https://gitea.pglikers.com/ai-program/penjent.git@latest
```

## 今後の方針について

バージョンの`1.2.0`より責任範囲を明確にするため
LLMとエージェントの機能を絞りました。

* アダプタ関連機能を削除しました。
* タスク関連機能を削除しました、
* Agentのステータス管理はセッションクラス(Session)に委任しました。

AIエージェントの補助機能については別ライブラリで提供してきます
