import pytest
from pengent.core.sessions.session_service.session_service_base import (
    SessionServiceBase,
)
from pengent.type.llm.llm_message import LLMMessage


class TestSessionServiceBase:
    """SessionServiceBaseクラスのテスト"""

    @pytest.fixture
    def base_service(self):
        """基底クラスのインスタンス"""
        return SessionServiceBase()

    def test_create_session_not_implemented(self, base_service):
        """create_sessionが未実装でNotImplementedErrorを発生させる"""
        with pytest.raises(NotImplementedError) as exc_info:
            base_service.create_session(user_id="user_001", session_id="session_001")
        assert "create_session method not implemented" in str(exc_info.value)

    def test_get_session_not_implemented(self, base_service):
        """get_sessionが未実装でNotImplementedErrorを発生させる"""
        with pytest.raises(NotImplementedError) as exc_info:
            base_service.get_session(user_id="user_001", session_id="session_001")
        assert "get_session method not implemented" in str(exc_info.value)

    def test_list_sessions_not_implemented(self, base_service):
        """list_sessionsが未実装でNotImplementedErrorを発生させる"""
        with pytest.raises(NotImplementedError) as exc_info:
            base_service.list_sessions(user_id="user_001")
        assert "list_sessions method not implemented" in str(exc_info.value)

    def test_delete_session_not_implemented(self, base_service):
        """delete_sessionが未実装でNotImplementedErrorを発生させる"""
        with pytest.raises(NotImplementedError) as exc_info:
            base_service.delete_session(user_id="user_001", session_id="session_001")
        assert "delete_session method not implemented" in str(exc_info.value)

    def test_append_events_message(self, base_service):
        """append_events_messageは実装されており、正常に動作する"""
        # Mockセッションを作成
        from unittest.mock import Mock
        from pengent.core.message_memory import HistoryMessageMemory

        session = Mock()
        session.events = HistoryMessageMemory()

        messages = [
            LLMMessage(role="user", content="Test message 1"),
            LLMMessage(role="assistant", content="Test message 2"),
        ]

        # メッセージを追加
        base_service.append_events_message(session, messages)

        # メッセージが追加されたことを確認
        assert len(session.events.messages) == 2
        assert session.events.messages[0].content == "Test message 1"
        assert session.events.messages[1].content == "Test message 2"

    def test_append_events_message_empty_list(self, base_service):
        """空のメッセージリストを追加"""
        from unittest.mock import Mock
        from pengent.core.message_memory import HistoryMessageMemory

        session = Mock()
        session.events = HistoryMessageMemory()

        base_service.append_events_message(session, [])

        assert len(session.events.messages) == 0

    def test_append_events_message_multiple_calls(self, base_service):
        """複数回メッセージを追加"""
        from unittest.mock import Mock
        from pengent.core.message_memory import HistoryMessageMemory

        session = Mock()
        session.events = HistoryMessageMemory()

        messages1 = [LLMMessage(role="user", content="First")]
        messages2 = [LLMMessage(role="assistant", content="Second")]

        base_service.append_events_message(session, messages1)
        base_service.append_events_message(session, messages2)

        assert len(session.events.messages) == 2
        assert session.events.messages[0].content == "First"
        assert session.events.messages[1].content == "Second"
