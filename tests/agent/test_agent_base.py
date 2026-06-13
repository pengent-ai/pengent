import pytest
from unittest.mock import Mock
from pengent.agents.agent_base import AgentBase
from pengent.type.agent.agent_enum import AgentSendOutput, AgentSendInput
from pengent.type.llm.llm_response import LLMResponse
from pengent.core.sessions.session import Session
import json


class DummyOutput:
    """ダミーのAgentSendOutputクラス"""

    @classmethod
    def dumps_schema(cls):
        return '{"type": "object", "properties": {"message": {"type": "string"}}}'

    @classmethod
    def dumps_example(cls, is_contents_type=False):
        return '{"message": "これはサンプルです"}'

    @classmethod
    def get_constraints(cls):
        return ["必ず'message'キーを含めてください"]

    @classmethod
    def from_dict(cls, data):
        return AgentSendOutput(message=data.get("message"))


@pytest.fixture
def mock_llm():
    """LLMクライアントのモックを作成"""
    llm = Mock()
    llm.llm_type = "openai"
    llm.parse_json.return_value = {"message": "こんにちは"}

    response = Mock(spec=LLMResponse)
    response.get_message.return_value = "こんにちは"
    response.get_tools.return_value = None
    response.is_message.return_value = True

    llm.request.return_value = response
    return llm


@pytest.fixture
def agent(mock_llm):
    """テスト用のエージェントを作成"""
    ag = AgentBase(name="test_agent", llm_client=mock_llm)
    return ag


@pytest.fixture
def session():
    """テスト用のセッションを作成"""
    return Session(session_id="test-session-123", user_id="test-user-456")


# ===== 基本機能のテスト =====


def test_agent_initialization():
    """エージェントの初期化テスト"""
    agent = AgentBase(name="test_agent")
    assert agent.name == "test_agent"
    assert agent.llm_client is None
    assert agent.params == {}


def test_agent_initialization_with_params():
    """パラメータ付きエージェントの初期化テスト"""
    params = {"temperature": 0.7, "max_tokens": 100}
    agent = AgentBase(name="test_agent", params=params)
    assert agent.params == params


def test_set_llm_client(agent, mock_llm):
    """LLMクライアントの設定テスト"""
    new_llm = Mock()
    agent.set_llm_client(new_llm)
    assert agent.llm_client == new_llm


# ===== メッセージ送信のテスト =====


async def test_send_with_string_input(agent):
    """文字列入力でのメッセージ送信テスト"""
    result = await agent.send("こんにちは")
    assert isinstance(result, AgentSendOutput)
    assert result.message == "こんにちは"


async def test_send_with_dict_input(agent):
    """辞書入力でのメッセージ送信テスト"""
    result = await agent.send({"content": "こんにちは"})
    assert isinstance(result, AgentSendOutput)
    assert result.message == "こんにちは"


async def test_send_with_agent_send_input(agent):
    """AgentSendInput入力でのメッセージ送信テスト"""
    input_data = AgentSendInput(content="こんにちは")
    result = await agent.send(input_data)
    assert isinstance(result, AgentSendOutput)
    assert result.message == "こんにちは"


async def test_send_with_session(agent, session):
    """セッション付きメッセージ送信テスト"""
    result = await agent.send("こんにちは", session=session)
    assert isinstance(result, AgentSendOutput)
    assert result.message == "こんにちは"


async def test_send_creates_session_if_none(agent):
    """セッションがない場合に自動作成されるテスト"""
    result = await agent.send("こんにちは", session=None)
    assert isinstance(result, AgentSendOutput)


# ===== システムプロンプトのテスト =====


def test_set_system_prompt(agent):
    """システムプロンプトの設定テスト"""
    custom_prompt = "これはカスタムシステムプロンプトです"
    agent.set_system_prompt(custom_prompt)
    assert agent.params["system_prompt"] == custom_prompt
    assert agent.system_prompt == custom_prompt


def test_system_prompt_generation(agent):
    """システムプロンプト生成テスト"""
    prompt = agent.system_prompt
    assert "Role" in prompt
    assert "Output" in prompt


# ===== パラメータ管理のテスト =====


def test_update_param(agent):
    """パラメータ更新テスト"""
    agent.update_param("temperature", 0.8)
    assert agent.params["temperature"] == 0.8


def test_clear_param(agent):
    """パラメータクリアテスト"""
    agent.update_param("temperature", 0.8)
    assert "temperature" in agent.params

    agent.clear_param("temperature")
    assert "temperature" not in agent.params


def test_get_value_for_kwargs(agent):
    """kwargs値取得テスト"""
    agent.params["default_value"] = "from_params"

    # kwargsから取得
    result = agent.get_value_for_kwargs(
        "test_key", default="default", test_key="from_kwargs"
    )
    assert result == "from_kwargs"

    # paramsから取得
    result = agent.get_value_for_kwargs("default_value", default="default")
    assert result == "from_params"

    # デフォルト値を使用
    result = agent.get_value_for_kwargs("nonexistent", default="default")
    assert result == "default"


# ===== エラーハンドリングのテスト =====


async def test_send_with_llm_error(agent, mock_llm):
    """LLMエラー時のハンドリングテスト"""
    mock_llm.request.side_effect = Exception("LLM Error")

    with pytest.raises(Exception) as exc_info:
        await agent.send("こんにちは")
    assert "LLM Error" in str(exc_info.value)


async def test_parse_error_with_retry(agent, mock_llm):
    """パースエラー時のリトライテスト"""
    # パースに失敗するレスポンスを設定
    agent.params["retry_max_count"] = 2
    agent.params["retry_delay_sec"] = 0
    agent.format = "application/json"  # JSON形式に設定

    response_fail = Mock(spec=LLMResponse)
    response_fail.get_message.return_value = "invalid json"
    response_fail.get_tools.return_value = None
    response_fail.is_message.return_value = True

    response_success = Mock(spec=LLMResponse)
    response_success.get_message.return_value = '{"message": "success after retry"}'
    response_success.get_tools.return_value = None
    response_success.is_message.return_value = True

    mock_llm.request.side_effect = [response_fail, response_success]
    mock_llm.parse_json.side_effect = [
        json.JSONDecodeError("test", "doc", 0),
        {"message": "success after retry"},
    ]

    result = await agent.send("こんにちは")
    assert result.message == "success after retry"


# ===== メッセージコールバックのテスト =====


async def test_message_callback(agent):
    """メッセージコールバックのテスト"""
    callback_called = {"called": False, "output": None}

    def callback(messages, output):
        callback_called["called"] = True
        callback_called["output"] = output

    agent.message_callback = callback
    result = await agent.send("こんにちは")

    assert callback_called["called"] is True
    assert callback_called["output"] == result


# ===== runメソッドのテスト =====


async def test_run_method(agent, session):
    """runメソッドのテスト"""
    result = await agent.run(session, "こんにちは")
    assert isinstance(result, AgentSendOutput)
    assert result.message == "こんにちは"
