import pytest
from unittest.mock import Mock
from pengent.agents.agent_base import AgentBase
from pengent.type.agent.agent_enum import AgentSendOutput
from pengent.type.llm.llm_response import LLMResponse
from pengent.type.llm.llm_message import LLMMessageTool, LLMMessageToolFunction
from pengent.core.sessions.session import Session
from pengent.type.tool.tool_enum import ToolBase, FunctionTool
from pengent.tools import ToolUtils
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


class MockTool(ToolBase):
    """テスト用のモックツール"""

    def __init__(self, name="test_tool", description="Test tool"):
        self.name = name
        self.description = description
        self.call_count = 0
        self.last_args = None

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {"query": {"type": "string"}, "count": {"type": "integer"}},
            "required": ["query"],
        }

    def run(self, **kwargs):
        self.call_count += 1
        self.last_args = kwargs
        return {"result": f"Tool executed with {kwargs}"}


class ErrorTool(ToolBase):
    """エラーを発生させるツール"""

    def __init__(self):
        self.name = "error_tool"
        self.description = "Tool that raises an error"

    def parameters_schema(self) -> dict:
        return {"type": "object", "properties": {}}

    def run(self, **kwargs):
        raise RuntimeError("Tool execution failed")


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


# ===== ツール追加のテスト =====


def test_add_tool(agent):
    """エージェントへのツール追加テスト"""
    tool = MockTool()
    agent.add_tool(tool)
    assert len(agent.tools) == 1
    assert agent.tools[0] == tool


def test_add_multiple_tools(agent):
    """複数のツール追加テスト"""
    tool1 = MockTool(name="tool1")
    tool2 = MockTool(name="tool2")

    agent.add_tool(tool1)
    agent.add_tool(tool2)

    assert len(agent.tools) == 2
    assert agent.tools[0] == tool1
    assert agent.tools[1] == tool2


def test_set_tools_with_list(agent, session):
    """runメソッドでツールが正規化される"""
    tool1 = MockTool(name="tool1")
    tool2 = MockTool(name="tool2")

    agent.tools = [tool1, tool2]

    # runメソッドでツールが正規化される
    response = Mock(spec=LLMResponse)
    response.get_message.return_value = '{"message": "test"}'
    response.get_tools.return_value = None
    response.is_message.return_value = True
    agent.llm_client.request.return_value = response

    agent.run(session, "test")

    # ツール設定が行われたか確認
    assert agent.llm_client.tools is not None
    assert len(agent.llm_client.tools) == 2


def test_function_tool_creation():
    """関数からのFunctionToolの作成テスト"""

    def my_function(x: int, y: int) -> int:
        """二つの数を足す関数"""
        return x + y

    # callableはFunctionToolとして正規化される
    tools = ToolUtils.normalize_tools([my_function])
    assert len(tools) == 1
    assert isinstance(tools[0], FunctionTool)


def test_tool_normalization():
    """ツール正規化テスト"""
    tool = MockTool()

    # 単一のToolBaseをリストにして正規化
    normalized = ToolUtils.normalize_tools([tool])

    assert len(normalized) == 1
    assert isinstance(normalized[0], ToolBase)
    assert normalized[0].name == "test_tool"


def test_duplicate_tool_names_error():
    """重複するツール名エラーテスト"""
    tool1 = MockTool(name="duplicate_tool")
    tool2 = MockTool(name="duplicate_tool")

    with pytest.raises(ValueError) as exc_info:
        ToolUtils.normalize_tools([tool1, tool2])
    assert "Duplicate tool names" in str(exc_info.value)


# ===== ツール実行のテスト =====


def test_execute_tool(agent, mock_llm):
    """ツール実行テスト"""
    tool = MockTool(name="test_tool")
    agent.add_tool(tool)

    # ツール呼び出しをシミュレート
    result = ToolUtils.execute_tool(tool, {"query": "test", "count": 5})

    assert result == {"result": "Tool executed with {'query': 'test', 'count': 5}"}
    assert tool.call_count == 1
    assert tool.last_args == {"query": "test", "count": 5}


def test_execute_tool_with_different_params(agent):
    """異なるパラメータでのツール実行テスト"""
    tool = MockTool()

    ToolUtils.execute_tool(tool, {"query": "search1"})
    ToolUtils.execute_tool(tool, {"query": "search2", "count": 10})

    assert tool.call_count == 2
    assert tool.last_args == {"query": "search2", "count": 10}


# ===== ツール呼び出しハンドリングのテスト =====


def test_handle_tools_call(agent, session):
    """ツール呼び出しハンドリングテスト"""
    tool = MockTool(name="test_tool")
    agent.add_tool(tool)

    # 初回のrunで_tool_mapを初期化
    response_init = Mock(spec=LLMResponse)
    response_init.get_message.return_value = '{"message": "initial"}'
    response_init.get_tools.return_value = None
    response_init.is_message.return_value = True
    agent.llm_client.request.return_value = response_init

    agent.run(session, "test")

    # ツール呼び出しをシミュレート
    tool_call = LLMMessageTool(
        id="call_123",
        function=LLMMessageToolFunction(
            name="test_tool", arguments={"query": "search_query"}
        ),
    )

    response_with_tools = Mock(spec=LLMResponse)
    response_with_tools.get_message.return_value = '{"message": "tool result"}'
    response_with_tools.get_tools.return_value = [tool_call]
    response_with_tools.is_message.return_value = True

    response_after_tool = Mock(spec=LLMResponse)
    response_after_tool.get_message.return_value = '{"message": "final response"}'
    response_after_tool.get_tools.return_value = None
    response_after_tool.is_message.return_value = True

    agent.llm_client.request.side_effect = [response_after_tool]

    # handle_tools_callを実行
    messages = []
    agent.handle_tools_call(session, messages, [tool_call])

    # ツールが実行されたか確認
    assert tool.call_count == 1
    assert tool.last_args == {"query": "search_query"}


def test_handle_multiple_tool_calls(agent, session):
    """複数のツール呼び出しハンドリングテスト"""
    tool1 = MockTool(name="tool1")
    tool2 = MockTool(name="tool2")
    agent.add_tool(tool1)
    agent.add_tool(tool2)

    # 初期化
    response_init = Mock(spec=LLMResponse)
    response_init.get_message.return_value = '{"message": "init"}'
    response_init.get_tools.return_value = None
    response_init.is_message.return_value = True
    agent.llm_client.request.return_value = response_init

    agent.run(session, "test")

    # 複数のツール呼び出し
    tool_call1 = LLMMessageTool(
        id="call_1",
        function=LLMMessageToolFunction(name="tool1", arguments={"query": "q1"}),
    )
    tool_call2 = LLMMessageTool(
        id="call_2",
        function=LLMMessageToolFunction(name="tool2", arguments={"query": "q2"}),
    )

    response_final = Mock(spec=LLMResponse)
    response_final.get_message.return_value = '{"message": "final"}'
    response_final.get_tools.return_value = None
    response_final.is_message.return_value = True

    agent.llm_client.request.side_effect = [response_final, response_final]

    messages = []
    agent.handle_tools_call(session, messages, [tool_call1, tool_call2])

    assert tool1.call_count == 1
    assert tool2.call_count == 1


def test_tool_call_message_registration(agent, session):
    """ツール呼び出しメッセージ登録テスト"""
    tool = MockTool(name="test_tool")
    agent.add_tool(tool)

    # 初期化
    response_init = Mock(spec=LLMResponse)
    response_init.get_message.return_value = '{"message": "init"}'
    response_init.get_tools.return_value = None
    response_init.is_message.return_value = True
    agent.llm_client.request.return_value = response_init

    agent.run(session, "test")

    # ツール呼び出しを作成
    tool_call = LLMMessageTool(
        id="call_123",
        function=LLMMessageToolFunction(name="test_tool", arguments={"query": "test"}),
    )

    response_final = Mock(spec=LLMResponse)
    response_final.get_message.return_value = '{"message": "result"}'
    response_final.get_tools.return_value = None
    response_final.is_message.return_value = True

    agent.llm_client.request.side_effect = [response_final]

    messages = []
    agent._register_tools_call(messages, [tool_call])

    # メッセージが登録されたか確認
    assert len(messages) == 1
    assert messages[0].role == "assistant"


def test_tool_call_result_message(agent, session):
    """ツール呼び出し結果メッセージテスト"""
    tool = MockTool(name="test_tool")
    agent.add_tool(tool)

    # 初期化
    response_init = Mock(spec=LLMResponse)
    response_init.get_message.return_value = '{"message": "init"}'
    response_init.get_tools.return_value = None
    response_init.is_message.return_value = True
    agent.llm_client.request.return_value = response_init

    agent.run(session, "test")

    # ツール呼び出し
    tool_call = LLMMessageTool(
        id="call_123",
        function=LLMMessageToolFunction(name="test_tool", arguments={"query": "test"}),
    )

    response_final = Mock(spec=LLMResponse)
    response_final.get_message.return_value = '{"message": "final"}'
    response_final.get_tools.return_value = None
    response_final.is_message.return_value = True

    agent.llm_client.request.side_effect = [response_final]

    messages = []
    agent._exec_tool_call(session, messages, tool_call)

    # 結果メッセージが追加されたか確認
    assert len(messages) >= 1


# ===== エラーハンドリング =====


def test_tool_not_found_in_agent(agent, session):
    """ツールが見つからない場合のエラーハンドリング"""
    tool = MockTool(name="existing_tool")
    agent.add_tool(tool)

    # 初期化
    response_init = Mock(spec=LLMResponse)
    response_init.get_message.return_value = '{"message": "init"}'
    response_init.get_tools.return_value = None
    response_init.is_message.return_value = True
    agent.llm_client.request.return_value = response_init

    agent.run(session, "test")

    # 存在しないツールを呼び出し
    missing_tool_call = LLMMessageTool(
        id="call_missing",
        function=LLMMessageToolFunction(name="nonexistent_tool", arguments={}),
    )

    response_final = Mock(spec=LLMResponse)
    response_final.get_message.return_value = '{"message": "error handled"}'
    response_final.get_tools.return_value = None
    response_final.is_message.return_value = True

    agent.llm_client.request.side_effect = [response_final]

    messages = []
    # ツール実行時のエラーをキャッチ
    result = agent._exec_tool_call(session, messages, missing_tool_call)

    # エラーメッセージが含まれることを確認
    assert "error" in str(result.get_message()).lower() or result.is_message()


def test_tool_execution_error(agent, session):
    """ツール実行エラーテスト"""
    error_tool = ErrorTool()
    agent.add_tool(error_tool)

    # 初期化
    response_init = Mock(spec=LLMResponse)
    response_init.get_message.return_value = '{"message": "init"}'
    response_init.get_tools.return_value = None
    response_init.is_message.return_value = True
    agent.llm_client.request.return_value = response_init

    agent.run(session, "test")

    LLMMessageTool(
        id="call_error",
        function=LLMMessageToolFunction(name="error_tool", arguments={}),
    )

    response_final = Mock(spec=LLMResponse)
    response_final.get_message.return_value = '{"message": "error handled"}'
    response_final.get_tools.return_value = None
    response_final.is_message.return_value = True

    agent.llm_client.request.side_effect = [response_final]

    # ツール実行エラーをキャッチ
    with pytest.raises(RuntimeError):
        ToolUtils.execute_tool(error_tool, {})


# ===== ツール出力のシリアライズテスト =====


def test_tool_dump_schema(agent):
    """ツールスキーマダンプテスト"""
    tool = MockTool()
    dumped = tool.dump()

    assert "type" in dumped
    assert dumped["type"] == "function"
    assert "function" in dumped
    assert dumped["function"]["name"] == "test_tool"
    assert dumped["function"]["description"] == "Test tool"
    assert "parameters" in dumped["function"]


def test_tool_json_serialization(agent):
    """ツールJSON シリアライゼーションテスト"""
    tool = MockTool()
    dumped = tool.dump()

    # JSONにシリアライズ可能か確認
    json_str = json.dumps(dumped)
    assert json_str is not None

    # デシリアライズ可能か確認
    deserialized = json.loads(json_str)
    assert deserialized == dumped
