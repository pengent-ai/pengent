"""
LLMから連続してtoolが投げられた場合のテスト

receive_message() の while True ループによる
複数回のツール呼び出し対応をテストする。
"""

import pytest
from unittest.mock import Mock
from pengent.agents.agent_base import AgentBase
from pengent.type.llm.llm_response import LLMResponse
from pengent.type.llm.llm_message import LLMMessageTool, LLMMessageToolFunction
from pengent.core.sessions.session import Session
from pengent.type.tool.tool_enum import ToolBase
from pengent.type.agent.agent_enum import ExecutionContext


class CountTool(ToolBase):
    """呼び出し回数を記録するツール"""

    def __init__(self, name="count_tool"):
        self.name = name
        self.description = "Counting tool"
        self.call_count = 0

    def parameters_schema(self) -> dict:
        return {"type": "object", "properties": {"query": {"type": "string"}}}

    def run(self, **kwargs):
        self.call_count += 1
        return {"result": f"executed #{self.call_count}"}


def _make_tool_response(tool_name="count_tool", tool_id="call_1", args=None):
    """ツール呼び出しを含むレスポンスモックを生成"""
    if args is None:
        args = {"query": "test"}
    tool_call = LLMMessageTool(
        id=tool_id,
        function=LLMMessageToolFunction(name=tool_name, arguments=args),
    )
    response = Mock(spec=LLMResponse)
    response.get_tools.return_value = [tool_call]
    response.is_message.return_value = False
    response.get_message.return_value = None
    return response, tool_call


def _make_message_response(message="最終回答"):
    """テキストメッセージのみを含むレスポンスモックを生成"""
    response = Mock(spec=LLMResponse)
    response.get_tools.return_value = None
    response.is_message.return_value = True
    response.get_message.return_value = message
    return response


@pytest.fixture
def mock_llm():
    llm = Mock()
    llm.llm_type = "openai"
    llm.parse_json.return_value = {"message": "テスト"}
    return llm


@pytest.fixture
def agent(mock_llm):
    return AgentBase(name="test_agent", llm_client=mock_llm)


@pytest.fixture
def session():
    return Session(session_id="test-session", user_id="test-user")


# ===== 連続ツール呼び出しのテスト =====


async def test_consecutive_tool_calls_twice(agent, session):
    """LLMがツールを2回連続して呼び出し、最後にメッセージを返す場合"""
    tool = CountTool()
    agent.add_tool(tool)

    tool_response1, _ = _make_tool_response(tool_id="call_1")
    tool_response2, _ = _make_tool_response(tool_id="call_2")
    final_response = _make_message_response("2回ツールを使った後の回答")

    # send()で1回目のリクエスト → tool_response1
    # _exec_tool_call_response で2回目リクエスト → tool_response2
    # _exec_tool_call_response で3回目リクエスト → final_response
    agent.llm_client.request.side_effect = [
        tool_response1,
        tool_response2,
        final_response,
    ]

    result = await agent.run(session, "テスト")

    assert result is not None
    assert result.message == "2回ツールを使った後の回答"
    assert tool.call_count == 2
    assert agent.llm_client.request.call_count == 3


async def test_consecutive_tool_calls_three_times(agent, session):
    """LLMがツールを3回連続して呼び出す場合"""
    tool = CountTool()
    agent.add_tool(tool)

    tool_response1, _ = _make_tool_response(tool_id="call_1")
    tool_response2, _ = _make_tool_response(tool_id="call_2")
    tool_response3, _ = _make_tool_response(tool_id="call_3")
    final_response = _make_message_response("3回ツールを使った後の回答")

    agent.llm_client.request.side_effect = [
        tool_response1,
        tool_response2,
        tool_response3,
        final_response,
    ]

    result = await agent.run(session, "テスト")

    assert result.message == "3回ツールを使った後の回答"
    assert tool.call_count == 3
    assert agent.llm_client.request.call_count == 4


async def test_single_tool_call_still_works(agent, session):
    """1回だけのツール呼び出し（既存の動作）が引き続き機能することを確認"""
    tool = CountTool()
    agent.add_tool(tool)

    tool_response, _ = _make_tool_response(tool_id="call_1")
    final_response = _make_message_response("1回のツール呼び出しの回答")

    agent.llm_client.request.side_effect = [tool_response, final_response]

    result = await agent.run(session, "テスト")

    assert result.message == "1回のツール呼び出しの回答"
    assert tool.call_count == 1
    assert agent.llm_client.request.call_count == 2


async def test_no_tool_call_still_works(agent, session):
    """ツール呼び出しなしでメッセージのみ返す場合（既存の動作）"""
    final_response = _make_message_response("ツールなしの回答")
    agent.llm_client.request.return_value = final_response

    result = await agent.run(session, "テスト")

    assert result.message == "ツールなしの回答"
    assert agent.llm_client.request.call_count == 1


# ===== max_tool_call_count のテスト =====


async def test_tool_call_limit_exceeded_raises_error(agent, session):
    """max_tool_call_count (デフォルト10) を超えるとValueErrorが発生する"""
    tool = CountTool()
    agent.add_tool(tool)

    # 11回分のツールレスポンスを用意
    tool_responses = [
        _make_tool_response(tool_id=f"call_{i}")[0] for i in range(11)
    ]
    agent.llm_client.request.side_effect = tool_responses

    with pytest.raises(ValueError) as exc_info:
        await agent.run(session, "テスト")

    assert "tool call limit exceeded" in str(exc_info.value)
    assert "10" in str(exc_info.value)


async def test_custom_max_tool_call_count(session, mock_llm):
    """paramsでmax_tool_call_countを指定した場合の制限テスト"""
    agent = AgentBase(
        name="limited_agent",
        llm_client=mock_llm,
        params={"max_tool_call_count": 2},
    )
    tool = CountTool()
    agent.add_tool(tool)

    # 3回分のツールレスポンスを用意（制限2なので3回目でエラー）
    tool_responses = [
        _make_tool_response(tool_id=f"call_{i}")[0] for i in range(3)
    ]
    mock_llm.request.side_effect = tool_responses

    with pytest.raises(ValueError) as exc_info:
        await agent.run(session, "テスト")

    assert "tool call limit exceeded" in str(exc_info.value)
    assert "2" in str(exc_info.value)


async def test_max_tool_call_count_exactly_at_limit(session, mock_llm):
    """ツール呼び出しがmax_tool_call_countちょうどの場合は成功する"""
    agent = AgentBase(
        name="exact_limit_agent",
        llm_client=mock_llm,
        params={"max_tool_call_count": 3},
    )
    tool = CountTool()
    agent.add_tool(tool)

    # 3回ツール呼び出し + 最終メッセージ
    tool_responses = [
        _make_tool_response(tool_id=f"call_{i}")[0] for i in range(3)
    ]
    final_response = _make_message_response("制限ちょうどの回答")
    mock_llm.request.side_effect = tool_responses + [final_response]

    result = await agent.run(session, "テスト")

    assert result.message == "制限ちょうどの回答"
    assert tool.call_count == 3


async def test_max_tool_call_count_zero_means_no_limit(session, mock_llm):
    """max_tool_call_count=0の場合は制限なし"""
    agent = AgentBase(
        name="no_limit_agent",
        llm_client=mock_llm,
        params={"max_tool_call_count": 0},
    )
    tool = CountTool()
    agent.add_tool(tool)

    # 15回ツール呼び出し + 最終メッセージ（制限なしなのでエラーにならない）
    tool_responses = [
        _make_tool_response(tool_id=f"call_{i}")[0] for i in range(15)
    ]
    final_response = _make_message_response("制限なしの回答")
    mock_llm.request.side_effect = tool_responses + [final_response]

    result = await agent.run(session, "テスト")

    assert result.message == "制限なしの回答"
    assert tool.call_count == 15


# ===== 複数ツールを連続して呼び出すテスト =====


async def test_consecutive_calls_with_multiple_tools_per_round(session, mock_llm):
    """各ラウンドで複数のツールが呼ばれ、それが連続する場合"""
    agent = AgentBase(name="multi_tool_agent", llm_client=mock_llm)
    tool_a = CountTool(name="tool_a")
    tool_b = CountTool(name="tool_b")
    agent.add_tool(tool_a)
    agent.add_tool(tool_b)

    # ラウンド1: tool_a と tool_b の両方を呼び出す
    tool_call_a = LLMMessageTool(
        id="call_a1",
        function=LLMMessageToolFunction(name="tool_a", arguments={"query": "q1"}),
    )
    tool_call_b = LLMMessageTool(
        id="call_b1",
        function=LLMMessageToolFunction(name="tool_b", arguments={"query": "q2"}),
    )
    round1_response = Mock(spec=LLMResponse)
    round1_response.get_tools.return_value = [tool_call_a, tool_call_b]
    round1_response.is_message.return_value = False

    # tool_a実行後のレスポンス（まだtool_bがある）
    intermediate_response = Mock(spec=LLMResponse)
    intermediate_response.get_tools.return_value = None
    intermediate_response.is_message.return_value = True
    intermediate_response.get_message.return_value = "中間レスポンス"

    # ラウンド2: tool_aのみ呼び出す
    tool_call_a2 = LLMMessageTool(
        id="call_a2",
        function=LLMMessageToolFunction(name="tool_a", arguments={"query": "q3"}),
    )
    round2_response = Mock(spec=LLMResponse)
    round2_response.get_tools.return_value = [tool_call_a2]
    round2_response.is_message.return_value = False

    final_response = _make_message_response("全ツール実行完了")

    # tool_a → intermediate_response (ラウンド1-a)
    # tool_b → round2_response (ラウンド1-b, これがhandle_tools_callの戻り値)
    # tool_a → final_response (ラウンド2)
    mock_llm.request.side_effect = [
        round1_response,       # send()での初回リクエスト
        intermediate_response, # tool_a実行後 (ラウンド1の途中)
        round2_response,       # tool_b実行後 (ラウンド1の最終レスポンス)
        final_response,        # tool_a実行後 (ラウンド2の最終レスポンス)
    ]

    result = await agent.run(session, "テスト")

    assert result.message == "全ツール実行完了"
    assert tool_a.call_count == 2  # ラウンド1とラウンド2で各1回
    assert tool_b.call_count == 1  # ラウンド1のみ


# ===== receive_message を直接テスト =====


async def test_receive_message_consecutive_tools_directly(agent, session):
    """receive_messageを直接呼び出して連続ツール呼び出しをテスト"""
    tool = CountTool()
    agent.add_tool(tool)

    # _tool_map を初期化するために先にrunを呼んでおく
    init_response = _make_message_response("初期化")
    agent.llm_client.request.return_value = init_response
    await agent.run(session, "初期化")

    # 連続ツール呼び出しシナリオ
    tool_response1, _ = _make_tool_response(tool_id="call_r1")
    tool_response2, _ = _make_tool_response(tool_id="call_r2")
    final_response = _make_message_response("直接呼び出しの回答")

    agent.llm_client.request.side_effect = [tool_response2, final_response]

    ctx = ExecutionContext.create(session=session)
    messages = []
    result = await agent.receive_message(session, tool_response1, messages, context=ctx)

    assert result.message == "直接呼び出しの回答"
    assert tool.call_count == 2


async def test_receive_message_error_when_no_tools_no_message(agent, session):
    """ツールもメッセージもないレスポンスはValueErrorを発生させる"""
    # 初期化
    init_response = _make_message_response("初期化")
    agent.llm_client.request.return_value = init_response
    await agent.run(session, "初期化")

    # ツールもメッセージもないレスポンス
    bad_response = Mock(spec=LLMResponse)
    bad_response.get_tools.return_value = None
    bad_response.is_message.return_value = False

    ctx = ExecutionContext.create(session=session)
    with pytest.raises(ValueError) as exc_info:
        await agent.receive_message(session, bad_response, [], context=ctx)

    assert "no message" in str(exc_info.value)


async def test_tool_call_count_resets_per_receive_message_call(agent, session):
    """receive_message呼び出しごとにtool_call_countがリセットされる"""
    tool = CountTool()
    agent.add_tool(tool)

    # 初期化
    init_response = _make_message_response("初期化")
    agent.llm_client.request.return_value = init_response
    await agent.run(session, "初期化")

    # 1回目のreceive_message: ツール5回 → メッセージ
    tool_responses_1 = [
        _make_tool_response(tool_id=f"r1_call_{i}")[0] for i in range(5)
    ]
    final_1 = _make_message_response("1回目の最終回答")
    # 最初のtool_responseはreceive_messageに直接渡すので、side_effectからは残り4回+final
    agent.llm_client.request.side_effect = tool_responses_1[1:] + [final_1]
    ctx1 = ExecutionContext.create(session=session)
    result1 = await agent.receive_message(
        session, tool_responses_1[0], [], context=ctx1
    )
    assert result1.message == "1回目の最終回答"

    # 2回目のreceive_message: 再び5回のツール呼び出しが可能（カウントリセット）
    tool_responses_2 = [
        _make_tool_response(tool_id=f"r2_call_{i}")[0] for i in range(5)
    ]
    final_2 = _make_message_response("2回目の最終回答")
    agent.llm_client.request.side_effect = tool_responses_2[1:] + [final_2]
    ctx2 = ExecutionContext.create(session=session)
    result2 = await agent.receive_message(
        session, tool_responses_2[0], [], context=ctx2
    )
    assert result2.message == "2回目の最終回答"
