from datetime import datetime, timezone
from pengent.core.sessions.session import Session
from pengent.core.message_memory import HistoryMessageMemory
from pengent.type.llm.llm_message import LLMMessage


class TestSession:
    """Sessionクラスのテスト"""

    def test_session_creation(self):
        """セッションの基本的な作成"""
        session = Session(session_id="test_session_001", user_id="user_123")

        assert session.session_id == "test_session_001"
        assert session.user_id == "user_123"
        assert session.state == {}
        assert isinstance(session.events, HistoryMessageMemory)
        assert isinstance(session.created_at, datetime)
        assert session.last_updated_time == 0.0

    def test_session_with_state(self):
        """初期stateを持つセッションの作成"""
        initial_state = {"context": "conversation_start", "counter": 0}
        session = Session(
            session_id="test_session_002", user_id="user_456", state=initial_state
        )

        assert session.state == initial_state
        assert session.state["context"] == "conversation_start"
        assert session.state["counter"] == 0

    def test_session_with_custom_events(self):
        """カスタムメッセージメモリを持つセッションの作成"""
        memory = HistoryMessageMemory()
        message = LLMMessage(role="user", content="Hello")
        memory.add_message(message)

        session = Session(
            session_id="test_session_003", user_id="user_789", events=memory
        )

        assert len(session.events.messages) == 1
        assert session.events.messages[0].content == "Hello"

    def test_session_state_modification(self):
        """セッションのstate変更"""
        session = Session(
            session_id="test_session_004", user_id="user_abc", state={"count": 0}
        )

        session.state["count"] = 5
        session.state["new_key"] = "new_value"

        assert session.state["count"] == 5
        assert session.state["new_key"] == "new_value"

    def test_session_events_addition(self):
        """セッションにメッセージを追加"""
        session = Session(session_id="test_session_005", user_id="user_def")

        msg1 = LLMMessage(role="user", content="Message 1")
        msg2 = LLMMessage(role="assistant", content="Message 2")

        session.events.add_message(msg1)
        session.events.add_message(msg2)

        assert len(session.events.messages) == 2
        assert session.events.messages[0].content == "Message 1"
        assert session.events.messages[1].content == "Message 2"

    def test_session_created_at(self):
        """created_atが正しく設定されているか確認"""
        before = datetime.now(timezone.utc)
        session = Session(session_id="test_session_006", user_id="user_ghi")
        after = datetime.now(timezone.utc)

        assert before <= session.created_at <= after
        assert session.created_at.tzinfo == timezone.utc

    def test_session_last_updated_time(self):
        """last_updated_timeの変更"""
        session = Session(session_id="test_session_007", user_id="user_jkl")

        assert session.last_updated_time == 0.0

        import time

        current_time = time.time()
        session.last_updated_time = current_time

        assert session.last_updated_time == current_time
