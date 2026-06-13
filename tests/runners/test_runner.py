import pytest
from unittest.mock import Mock, AsyncMock
from pengent.core.runners.runner import Runner
from pengent.agents.agent_base import AgentBase
from pengent.core.sessions.session_service.in_memory_session_service import (
    InMemorySessionService,
)
from pengent.core.sessions.session import Session
from pengent.type.agent.agent_enum import AgentSendOutput
from pengent.type.llm.llm_message import LLMMessage


class TestRunner:
    """Runnerクラスのテスト"""

    @pytest.fixture
    def mock_agent(self):
        """モックエージェントを作成"""
        agent = Mock(spec=AgentBase)

        # run メソッドのモック出力
        output = Mock(spec=AgentSendOutput)
        output.events_messages = [
            LLMMessage(role="user", content="Test input"),
            LLMMessage(role="assistant", content="Test output"),
        ]
        output.message = "Test response"
        output.context = {}

        agent.run = AsyncMock(return_value=output)
        return agent

    @pytest.fixture
    def session_service(self):
        """実際のInMemorySessionServiceを使用"""
        return InMemorySessionService()

    @pytest.fixture
    def runner(self, mock_agent, session_service):
        """Runnerインスタンスを作成"""
        return Runner(agent=mock_agent, session_service=session_service)

    def test_runner_initialization(self, mock_agent, session_service):
        """Runnerの初期化"""
        runner = Runner(agent=mock_agent, session_service=session_service)

        assert runner.agent == mock_agent
        assert runner.session_service == session_service
        assert runner.memory_service is None
        assert runner.artifact_service is None

    def test_run_creates_new_session(self, runner, mock_agent):
        """セッションが存在しない場合、新しいセッションを作成"""
        runner.run(user_id="user_001", session_id="session_001", input="Hello")

        # セッションが作成されたことを確認
        session = runner.session_service.get_session(
            user_id="user_001", session_id="session_001"
        )
        assert session is not None
        assert session.user_id == "user_001"
        assert session.session_id == "session_001"

        # エージェントのrunメソッドが呼ばれたことを確認
        mock_agent.run.assert_called_once()
        call_args = mock_agent.run.call_args
        assert call_args.kwargs["input"] == "Hello"

    def test_run_uses_existing_session(self, runner, mock_agent):
        """既存のセッションがある場合、それを使用"""
        # セッションを事前に作成
        runner.session_service.create_session(
            user_id="user_002",
            session_id="session_002",
            state={"existing": "data"},
        )

        runner.run(user_id="user_002", session_id="session_002", input="Hello again")

        # エージェントが既存のセッションで呼ばれたことを確認
        mock_agent.run.assert_called_once()
        call_args = mock_agent.run.call_args
        session = call_args.kwargs["session"]
        assert session.state == {"existing": "data"}

    def test_run_appends_events_to_session(self, runner, mock_agent):
        """runの実行後、イベントメッセージがセッションに追加される"""
        runner.run(user_id="user_003", session_id="session_003", input="Test message")

        # セッションを取得
        session = runner.session_service.get_session(
            user_id="user_003", session_id="session_003"
        )

        # イベントメッセージが追加されていることを確認
        assert len(session.events.messages) == 2
        assert session.events.messages[0].content == "Test input"
        assert session.events.messages[1].content == "Test output"

    def test_run_returns_agent_output(self, runner, mock_agent):
        """runがエージェントの出力を返す"""
        result = runner.run(user_id="user_004", session_id="session_004", input="Test")

        assert result is not None
        assert result.message == "Test response"

    def test_run_multiple_times_same_session(self, runner, mock_agent):
        """同じセッションで複数回runを実行"""
        # 1回目
        runner.run(user_id="user_005", session_id="session_005", input="First message")

        # 2回目(新しい出力を設定)
        output2 = Mock(spec=AgentSendOutput)
        output2.events_messages = [
            LLMMessage(role="user", content="Second input"),
            LLMMessage(role="assistant", content="Second output"),
        ]
        output2.message = "Second response"
        output2.context = {}
        mock_agent.run.return_value = output2

        runner.run(
            user_id="user_005",
            session_id="session_005",
            input="Second message",
        )

        # セッションを取得
        session = runner.session_service.get_session(
            user_id="user_005", session_id="session_005"
        )

        # 両方のメッセージが追加されていることを確認
        assert len(session.events.messages) == 4
        assert session.events.messages[0].content == "Test input"
        assert session.events.messages[1].content == "Test output"
        assert session.events.messages[2].content == "Second input"
        assert session.events.messages[3].content == "Second output"

    def test_run_with_different_users(self, runner, mock_agent):
        """異なるユーザーでrunを実行"""
        runner.run(
            user_id="user_006",
            session_id="session_shared",
            input="User 6 message",
        )

        runner.run(
            user_id="user_007",
            session_id="session_shared",
            input="User 7 message",
        )

        # 各ユーザーのセッションが独立していることを確認
        session1 = runner.session_service.get_session(
            user_id="user_006", session_id="session_shared"
        )
        session2 = runner.session_service.get_session(
            user_id="user_007", session_id="session_shared"
        )

        assert session1 is not None
        assert session2 is not None
        assert session1 is not session2

    def test_run_with_kwargs(self, runner, mock_agent):
        """kwargsを使ってrunを実行"""
        result = runner.run(
            user_id="user_008",
            session_id="session_008",
            input="Test with kwargs",
            custom_param="custom_value",
        )

        # エージェントが呼ばれたことを確認
        mock_agent.run.assert_called_once()
        assert result is not None

    def test_run_session_passed_to_agent(self, runner, mock_agent):
        """エージェントにセッションが正しく渡されているか"""
        runner.run(
            user_id="user_009",
            session_id="session_009",
            input="Test session passing",
        )

        # エージェントのrunメソッドに渡された引数を確認
        call_args = mock_agent.run.call_args
        assert "session" in call_args.kwargs
        session = call_args.kwargs["session"]
        assert isinstance(session, Session)
        assert session.user_id == "user_009"
        assert session.session_id == "session_009"

    def test_run_empty_events_messages(self, runner, mock_agent):
        """イベントメッセージが空の場合"""
        # 空のイベントメッセージを持つ出力
        output = Mock(spec=AgentSendOutput)
        output.events_messages = []
        output.message = "Empty events"
        output.context = {}
        mock_agent.run.return_value = output

        result = runner.run(
            user_id="user_010",
            session_id="session_010",
            input="Test empty events",
        )

        # セッションを取得
        session = runner.session_service.get_session(
            user_id="user_010", session_id="session_010"
        )

        # イベントメッセージが追加されていないことを確認
        assert len(session.events.messages) == 0
        assert result.message == "Empty events"

    def test_runner_agent_attribute(self, runner, mock_agent):
        """Runnerのagent属性にアクセス"""
        assert runner.agent == mock_agent

    def test_runner_session_service_attribute(self, runner, session_service):
        """Runnerのsession_service属性にアクセス"""
        assert runner.session_service == session_service

    def test_run_with_session_state_delta(self, runner, mock_agent):
        """session_stateがcontextに含まれる場合、apply_state_deltaが呼ばれる"""
        # session_stateを含む出力を設定
        output = Mock(spec=AgentSendOutput)
        output.events_messages = []
        output.message = "Test with state"
        output.context = {
            "session_state": {
                "key1": "value1",
                "key2": "value2",
            }
        }
        mock_agent.run.return_value = output

        runner.run(
            user_id="user_011",
            session_id="session_011",
            input="Test state delta",
        )

        # セッションを取得
        session = runner.session_service.get_session(
            user_id="user_011", session_id="session_011"
        )

        # stateが更新されていることを確認
        assert session.state.get("key1") == "value1"
        assert session.state.get("key2") == "value2"

    def test_run_with_empty_context(self, runner, mock_agent):
        """contextがNoneまたは空の場合でもエラーにならない"""
        # contextがNoneの出力
        output = Mock(spec=AgentSendOutput)
        output.events_messages = []
        output.message = "Test with None context"
        output.context = None
        mock_agent.run.return_value = output

        result = runner.run(
            user_id="user_012",
            session_id="session_012",
            input="Test None context",
        )

        assert result.message == "Test with None context"

        # contextが空辞書の出力
        output.context = {}
        result = runner.run(
            user_id="user_012",
            session_id="session_012",
            input="Test empty context",
        )

        assert result is not None

    def test_runner_initialization_with_artifact_service(
        self, mock_agent, session_service
    ):
        """artifact_serviceを指定してRunnerを初期化"""
        mock_artifact_service = Mock()
        runner = Runner(
            agent=mock_agent,
            session_service=session_service,
            artifact_service=mock_artifact_service,
        )

        assert runner.artifact_service == mock_artifact_service

    def test_run_preserves_existing_session_state(self, runner, mock_agent):
        """既存のセッション状態が保持される"""
        # 既存の状態でセッションを作成
        runner.session_service.create_session(
            user_id="user_013",
            session_id="session_013",
            state={"existing_key": "existing_value"},
        )

        # 新しい状態を追加
        output = Mock(spec=AgentSendOutput)
        output.events_messages = []
        output.message = "Test preserve state"
        output.context = {
            "session_state": {
                "new_key": "new_value",
            }
        }
        mock_agent.run.return_value = output

        runner.run(
            user_id="user_013",
            session_id="session_013",
            input="Test",
        )

        # セッションを取得
        session = runner.session_service.get_session(
            user_id="user_013", session_id="session_013"
        )

        # 既存の状態と新しい状態が両方存在することを確認
        assert session.state.get("existing_key") == "existing_value"
        assert session.state.get("new_key") == "new_value"
