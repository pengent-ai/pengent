
* ToolUtils.execute_toolを非同期化しました。
  * [tool_utils.py](../../src/pengent/tools/tool_utils.py)

* AgentBase の主要メソッドを非同期化しました。
  * [agent_base.py](../../src/pengent/agents/agent_base.py)
  * `run`, `send`, `receive_message`, `handle_tools_call`, `_exec_tool_call`, `_exec_tool_call_response`, `_with_retry` を `async def` に変更
  * `import time` を削除し、`_with_retry` 内の `time.sleep` を `asyncio.sleep` に変更

* WorkerBase の主要メソッドを非同期化しました。
  * [worker_base.py](../../src/pengent/workers/worker_base.py)
  * `run`, `send`, `receive_message`, `handle_tools_call`, `_exec_tool_call`, `_exec_tool_call_worker_response` を `async def` に変更

* Runner に非同期エントリーポイントを追加しました。
  * [runner.py](../../src/pengent/core/runners/runner.py)
  * `run_async` を新規追加（非同期版）
  * 既存の `run` は `asyncio.run(run_async(...))` の同期ラッパーとして残す（後方互換）