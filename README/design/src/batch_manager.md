# BatchManager 設計書

**最終更新**: 

2025-08-22 Asia/Tokyo

**クラス目的**: 

LLMバッチ処理を管理する。
データの投入、送信、結果取得を安全に行うためのマネージャ

---

## 概要

BatchManager は以下の役割を持つ

* **MVP機能**
  * LLMBatchData の受け付け
    * enqueue
  * LLMクライアントごとにバッチ送信 
    * dispatch
  * 定期的にバッチ結果を取得する
    * check
  * 結果通知(callback)を実行する
 
### 運用モードの検討

* スケジューラ実行 dispatch\_once 例 APScheduler で毎時
* 常駐ディスパッチャスレッド start\_dispatcher 低遅延が必要な場合
* ハイブリッド しきい値 size 到達で即時 flush かつ 1時間毎の保険 flush

後から変更できるようにしたい。
とりあえずはスケジューラ実行を想定する

### 非機能

* 分散キューや分散ロックの実装
* 複数プロセス間の競合解決

---

## アーキテクチャ

**主要コンポーネント**

* BatchManager 本体
  * 受け渡しキュー inbox Queue\[LLMBatchData]
  * 内部処理キュー processing deque\[LLMBatchFileData]
  * 完了キュー completed deque\[LLMBatchFileData]
  * LLM クライアント実装 LLMBatchClient
    * 例 LLMOpenAIBatchClient LLMAnthropicBatchClient
  * コールバック群 List\[Callback]


