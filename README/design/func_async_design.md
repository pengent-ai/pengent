# AgentBase 非同期化設計

## 背景・動機

非同期ツール関数（`async def`） tool として登録した場合、現在の同期実装では以下の問題が発生する：

- `ToolUtils.execute_tool` → `tool.run()` → coroutine オブジェクトが返る（未 await）
- その coroutine が `json.dumps` でシリアライズされ `TypeError` になる

根本解決として、**エージェント全体を非同期化**する。

---

## 非同期化の対象と影響範囲

```
Runner.run()
  └── AgentBase.run()          ← async 化
        └── AgentBase.send()   ← async 化
              └── llm_client.request()           ← async 化 (async_request)
              └── AgentBase.receive_message()    ← async 化
                    └── AgentBase.handle_tools_call()   ← async 化
                          └── AgentBase._exec_tool_call()        ← async 化
                                └── ToolUtils.execute_tool()     ← async 化
                                └── AgentBase._exec_tool_call_response()  ← async 化
                                      └── llm_client.request()            ← async 化
              └── AgentBase._with_retry()        ← async 化
```

`WorkerBase` も同様のメソッド構造を持つため、同じスコープで非同期化する。

---

## 各レイヤーの変更方針

### 1. ToolUtils.execute_tool

sync/async 両方のツール関数を透過的に扱う。

```python
import inspect

@staticmethod
async def execute_tool(
    tool: ToolBase,
    parguments: dict,
    *,
    context: Optional[Any] = None,
) -> Any:
    kwargs = dict(parguments or {})
    if isinstance(tool, FunctionTool):
        if tool.has_tool_context():
            kwargs["tool_context"] = ToolContext.create(context)

    result = tool.run(**kwargs)
    # async 関数を透過的に扱う（FunctionTool.run は sync のまま）
    if inspect.iscoroutine(result):
        result = await result
    return result
```

`FunctionTool.run()` 自体は sync のままで良い。
呼び出し結果が coroutine かどうかを `execute_tool` 側で判定・await する。

---

### 2. LLMClientBase / LLMOpenAIClient

非同期リクエスト用のメソッドを追加する。
既存の `request()` (sync) はそのまま残し、**段階的移行**を可能にする。

```python
# llm_client_base.py
from abc import abstractmethod

class LLMClientBase:
    def request(self, ...) -> LLMResponse:  # 既存 sync（残す）
        ...

    async def arequest(self, ...) -> LLMResponse:  # 新規追加
        # デフォルト実装: sync を asyncio.to_thread でラップ
        import asyncio
        return await asyncio.to_thread(self.request, prompt=prompt, messages=messages, **kwargs)
```

`LLMOpenAIClient` は `AsyncOpenAI` クライアントを使う実装に切り替える：

```python
from openai import AsyncOpenAI

class LLMOpenAIClient(LLMClientBase):
    def __init__(self, ...):
        self.client = OpenAI(...)           # sync（既存）
        self.async_client = AsyncOpenAI(...)  # async 用

    async def async_request(self, ...) -> LLMResponse:
        # AsyncOpenAI を使って実装
        response = await self.async_client.chat.completions.create(...)
        return self._parse_response(response)
```

---

### 3. AgentBase の主要メソッド

すべて `async def` に変える。命名は変えず、そのまま async 化する。

```python
class AgentBase:

    async def run(self, session, input=None, ctx=None, **kwargs) -> AgentSendOutput:
        ...
        return await self.send(input, session, ctx, **kwargs)

    async def send(self, input=None, session=None, ctx=None, **kwargs):
        ...
        response = await self.llm_client.async_request(messages=...)
        return await self.receive_message(session, response, messages, context=ctx)

    async def receive_message(self, session, response, messages, *, context=None):
        while True:
            tools = response.get_tools()
            if tools:
                response = await self.handle_tools_call(session, messages, tools, context=context)
                continue
            ...
        response, output = await self._with_retry(session, response, messages)
        ...

    async def handle_tools_call(self, session, messages, tools, *, context=None):
        self._register_tools_call(messages, tools)  # sync のまま OK
        for tool in tools:
            response = await self._exec_tool_call(session, messages, tool, context=context)
        return response

    async def _exec_tool_call(self, session, messages, tool, *, context=None):
        ...
        result = await ToolUtils.execute_tool(tool_base, tool.function.arguments, context=context)
        return await self._exec_tool_call_response(session, result, messages, tool)

    async def _exec_tool_call_response(self, session, result, messages, tool):
        ...
        response = await self.llm_client.async_request(messages=session.events.get() + messages)
        return response

    async def _with_retry(self, session, response, messages):
        # time.sleep → asyncio.sleep に変更
        import asyncio
        ...
        await asyncio.sleep(retry_delay_sec)
        response = await self.llm_client.async_request(messages=...)
```

---

### 4. WorkerBase

`AgentBase` と同様に非同期化する。
`_exec_tool_call`、`handle_tools_call`、`_exec_tool_call_worker_response` を async にする。

---

### 5. Runner

エントリーポイントとして sync/async 両方を提供する。

```python
class Runner:

    async def run_async(self, *, user_id, session_id, input, **kwargs) -> AgentSendOutput:
        """非同期エントリーポイント（推奨）"""
        session = self._get_or_create_session(user_id, session_id)
        output = await self.agent.run(session=session, input=input, **kwargs)
        self._save_session(session, output)
        return output

    def run(self, *, user_id, session_id, input, **kwargs) -> AgentSendOutput:
        """同期エントリーポイント（後方互換）"""
        import asyncio
        return asyncio.run(self.run_async(user_id=user_id, session_id=session_id, input=input, **kwargs))
```

既存の sync `Runner.run()` を呼んでいるコードは変更不要。
新規コードは `await runner.run_async(...)` を使う。

---

## 段階的移行フェーズ

### Phase 1: ToolUtils.execute_tool を async 化
- `execute_tool` を `async def` に変更
- `FunctionTool.run()` は sync のまま
- sync/async ツール両方に対応

### Phase 2: AgentBase のツール実行パスを async 化
- `_exec_tool_call`、`_exec_tool_call_response`、`handle_tools_call` を async 化
- `llm_client` は `asyncio.to_thread` ラッパーで一時対応（`async_request` のデフォルト実装）

### Phase 3: LLMClient を本格 async 化
- `LLMOpenAIClient` に `AsyncOpenAI` を導入
- `async_request` をネイティブ実装に置き換え

### Phase 4: AgentBase 全体を async 化
- `run`、`send`、`receive_message`、`_with_retry` を async 化
- `time.sleep` → `asyncio.sleep`

### Phase 5: Runner を async 対応
- `run_async` を追加
- 既存 `run` は `asyncio.run` ラッパーとして残す

### Phase 6: WorkerBase を async 化
- AgentBase と同様に非同期化

---

## 後方互換性の方針

| 対象 | 方針 |
|------|------|
| `Runner.run()` | `asyncio.run(run_async(...))` として残す |
| `LLMClientBase.request()` | sync のまま残す（既存テスト向け） |
| `AgentBase.run()` | async 化（破壊的変更だが内部 API） |
| `FunctionTool.run()` | sync のまま |
| sync ツール関数 | `execute_tool` 内で透過的に対応 |

`AgentBase.run()` を async にすると、外部から呼ぶ側（例：Worker スレッド）での対応が必要になる。
`Runner.run()` を同期ラッパーとして維持することで、スレッドベースの呼び出し元への影響を最小化する。

---

## 注意点

- **`asyncio.run()` のネスト問題**：既にイベントループが動いている環境（FastAPI, Jupyter 等）では `asyncio.run()` が使えない。その場合は `asyncio.get_event_loop().run_until_complete()` または `nest_asyncio` で対処。
- **スレッドセーフ**：`_tool_map` のキャッシュ構築は初回のみなので問題なし。
- **`time.sleep` の置き換え**：`_with_retry` 内の `time.sleep` は `asyncio.sleep` に変更しないとイベントループをブロックする。
