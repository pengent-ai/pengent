import pytest
from pengent.core.sessions.session_service.in_memory_session_service import (
    InMemorySessionService,
)
from pengent.errors.already_exists_error import AlreadyExistsError
from pengent.type.llm.llm_message import LLMMessage


class TestInMemorySessionService:
    """InMemorySessionServiceクラスのテスト"""

    @pytest.fixture
    def service(self):
        """各テストで使用するサービスインスタンス"""
        return InMemorySessionService()

    def test_create_session(self, service):
        """セッションの作成"""
        session = service.create_session(user_id="user_001", session_id="session_001")

        assert session.session_id == "session_001"
        assert session.user_id == "user_001"
        assert session.state == {}

    def test_create_session_with_state(self, service):
        """初期stateを持つセッションの作成"""
        initial_state = {"key": "value"}
        session = service.create_session(
            user_id="user_002", session_id="session_002", state=initial_state
        )

        assert session.state == initial_state

    def test_create_duplicate_session_raises_error(self, service):
        """同じsession_idで2回作成しようとするとエラー"""
        service.create_session(user_id="user_003", session_id="session_003")

        with pytest.raises(AlreadyExistsError):
            service.create_session(user_id="user_003", session_id="session_003")

    def test_get_session(self, service):
        """セッションの取得"""
        service.create_session(user_id="user_004", session_id="session_004")

        session = service.get_session(user_id="user_004", session_id="session_004")

        assert session is not None
        assert session.session_id == "session_004"
        assert session.user_id == "user_004"

    def test_get_nonexistent_session(self, service):
        """存在しないセッションの取得"""
        session = service.get_session(
            user_id="nonexistent_user", session_id="nonexistent_session"
        )

        assert session is None

    def test_list_sessions(self, service):
        """ユーザーのセッション一覧の取得"""
        service.create_session(user_id="user_005", session_id="session_005_1")
        service.create_session(user_id="user_005", session_id="session_005_2")
        service.create_session(user_id="user_006", session_id="session_006_1")

        sessions = service.list_sessions(user_id="user_005")

        assert len(sessions) == 2
        session_ids = [s.session_id for s in sessions]
        assert "session_005_1" in session_ids
        assert "session_005_2" in session_ids

    def test_list_sessions_empty(self, service):
        """存在しないユーザーのセッション一覧"""
        sessions = service.list_sessions(user_id="nonexistent_user")

        assert sessions == []

    def test_delete_session(self, service):
        """セッションの削除"""
        service.create_session(user_id="user_007", session_id="session_007")

        # セッションが存在することを確認
        session = service.get_session(user_id="user_007", session_id="session_007")
        assert session is not None

        # 削除
        service.delete_session(user_id="user_007", session_id="session_007")

        # 削除されたことを確認
        session = service.get_session(user_id="user_007", session_id="session_007")
        assert session is None

    def test_delete_nonexistent_session(self, service):
        """存在しないセッションの削除(エラーにならないこと)"""
        # エラーが発生しないことを確認
        service.delete_session(
            user_id="nonexistent_user", session_id="nonexistent_session"
        )

    def test_delete_all_user_sessions(self, service):
        """ユーザーの全セッション削除後、ユーザーエントリも削除されるか"""
        service.create_session(user_id="user_008", session_id="session_008_1")
        service.create_session(user_id="user_008", session_id="session_008_2")

        # すべて削除
        service.delete_session(user_id="user_008", session_id="session_008_1")
        service.delete_session(user_id="user_008", session_id="session_008_2")

        # ユーザーエントリが削除されていることを確認
        assert "user_008" not in service.sessions

    def test_append_events_message(self, service):
        """セッションにメッセージを追加"""
        session = service.create_session(user_id="user_009", session_id="session_009")

        messages = [
            LLMMessage(role="user", content="Hello"),
            LLMMessage(role="assistant", content="Hi there!"),
        ]

        service.append_events_message(session, messages)

        assert len(session.events.messages) == 2
        assert session.events.messages[0].content == "Hello"
        assert session.events.messages[1].content == "Hi there!"

    def test_session_isolation(self, service):
        """異なるユーザーのセッションが隔離されているか"""
        service.create_session(user_id="user_010", session_id="session_shared")
        service.create_session(user_id="user_011", session_id="session_shared")

        session1 = service.get_session(user_id="user_010", session_id="session_shared")
        session2 = service.get_session(user_id="user_011", session_id="session_shared")

        assert session1 is not None
        assert session2 is not None
        assert session1.user_id != session2.user_id
        assert session1 is not session2
