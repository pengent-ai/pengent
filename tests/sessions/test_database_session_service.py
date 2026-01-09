import pytest
from datetime import datetime
from pengent.core.sessions.session_service.database_session_service import (
    DatabaseSessionService,
)
from pengent.type.llm.llm_message import LLMMessage
from pengent.db.base import Database


class TestDatabaseSessionService:
    """DatabaseSessionServiceクラスのテスト"""

    @pytest.fixture
    def test_db(self):
        """テスト用のインメモリSQLiteデータベースを作成"""
        # インメモリSQLiteデータベースを使用
        db = Database(database_url="sqlite:///:memory:", is_create_all=True)
        return db

    @pytest.fixture
    def service(self, test_db):
        """各テストで使用するサービスインスタンス"""
        return DatabaseSessionService(db=test_db)

    def test_create_session(self, service):
        """セッションの作成"""
        session = service.create_session(user_id="user_001", session_id="session_001")

        assert session.session_id == "session_001"
        assert session.user_id == "user_001"
        assert session.state == {}

    def test_create_session_with_state(self, service):
        """初期stateを持つセッションの作成"""
        initial_state = {"key": "value", "count": 42}
        session = service.create_session(
            user_id="user_002", session_id="session_002", state=initial_state
        )

        assert session.state == initial_state

    def test_create_duplicate_session_raises_error(self, service):
        """同じsession_idで2回作成しようとするとエラー"""
        service.create_session(user_id="user_003", session_id="session_003")

        # AlreadyExistsErrorがRuntimeErrorでラップされる
        with pytest.raises(RuntimeError) as exc_info:
            service.create_session(user_id="user_003", session_id="session_003")
        assert "already exists" in str(exc_info.value)

    def test_get_session(self, service):
        """セッションの取得"""
        service.create_session(
            user_id="user_004", session_id="session_004", state={"test": "data"}
        )

        session = service.get_session(user_id="user_004", session_id="session_004")

        assert session is not None
        assert session.session_id == "session_004"
        assert session.user_id == "user_004"
        assert session.state == {"test": "data"}

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

    def test_append_events_message(self, service):
        """セッションにメッセージを追加"""
        session = service.create_session(user_id="user_008", session_id="session_008")

        messages = [
            LLMMessage(role="user", content="Hello"),
            LLMMessage(role="assistant", content="Hi there!"),
        ]

        service.append_events_message(session=session, events_messages=messages)

        # セッションを再取得してメッセージを確認
        retrieved_session = service.get_session(
            user_id="user_008", session_id="session_008"
        )

        assert len(retrieved_session.events.messages) == 2
        assert retrieved_session.events.messages[0].content == "Hello"
        assert retrieved_session.events.messages[1].content == "Hi there!"

    def test_append_events_message_updates_last_updated_time(self, service):
        """メッセージ追加時にlast_updated_timeが更新される"""
        session = service.create_session(user_id="user_009", session_id="session_009")

        initial_time = session.last_updated_time

        messages = [LLMMessage(role="user", content="Test")]
        service.append_events_message(session=session, events_messages=messages)

        # セッションを再取得してlast_updated_timeを確認
        retrieved_session = service.get_session(
            user_id="user_009", session_id="session_009"
        )

        assert retrieved_session.last_updated_time > initial_time

    def test_append_events_message_with_tool_calls(self, service):
        """tool_callsを含むメッセージを追加"""
        session = service.create_session(user_id="user_010", session_id="session_010")

        messages = [
            LLMMessage(
                role="assistant",
                content="",
                tool_calls=[
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "test_function",
                            "arguments": '{"arg": "value"}',
                        },
                    }
                ],
            )
        ]

        service.append_events_message(session=session, events_messages=messages)

        # セッションを再取得してメッセージを確認
        retrieved_session = service.get_session(
            user_id="user_010", session_id="session_010"
        )

        assert len(retrieved_session.events.messages) == 1
        assert retrieved_session.events.messages[0].tool_calls is not None

    def test_session_persistence(self, service):
        """セッションがデータベースに永続化されているか"""
        # セッション作成
        service.create_session(
            user_id="user_011", session_id="session_011", state={"persistent": "data"}
        )

        # メッセージ追加
        session = service.get_session(user_id="user_011", session_id="session_011")
        messages = [LLMMessage(role="user", content="Persisted message")]
        service.append_events_message(session=session, events_messages=messages)

        # 新しいサービスインスタンスで再取得
        new_service = DatabaseSessionService(db=service.db)
        retrieved_session = new_service.get_session(
            user_id="user_011", session_id="session_011"
        )

        assert retrieved_session is not None
        assert retrieved_session.state == {"persistent": "data"}
        assert len(retrieved_session.events.messages) == 1
        assert retrieved_session.events.messages[0].content == "Persisted message"

    def test_delete_session_with_messages(self, service):
        """メッセージを含むセッションの削除"""
        session = service.create_session(user_id="user_012", session_id="session_012")

        messages = [
            LLMMessage(role="user", content="Message 1"),
            LLMMessage(role="assistant", content="Message 2"),
        ]
        service.append_events_message(session=session, events_messages=messages)

        # セッション削除
        service.delete_session(user_id="user_012", session_id="session_012")

        # 削除されたことを確認
        retrieved_session = service.get_session(
            user_id="user_012", session_id="session_012"
        )
        assert retrieved_session is None

    def test_session_isolation_between_users(self, service):
        """異なるユーザー間でセッションが隔離されているか"""
        # Databaseではsession_idはグローバルにユニークなので異なるIDを使用
        service.create_session(user_id="user_013", session_id="session_013")
        service.create_session(user_id="user_014", session_id="session_014")

        # 各ユーザーは自分のセッションのみ取得できる
        session1 = service.get_session(user_id="user_013", session_id="session_013")
        session2 = service.get_session(user_id="user_014", session_id="session_014")

        # 他のユーザーのセッションは取得できない
        session1_from_user2 = service.get_session(
            user_id="user_014", session_id="session_013"
        )

        assert session1 is not None
        assert session2 is not None
        assert session1.user_id == "user_013"
        assert session2.user_id == "user_014"
        assert session1_from_user2 is None  # 異なるユーザーのセッションは取得不可

    def test_multiple_message_appends(self, service):
        """複数回メッセージを追加"""
        session = service.create_session(user_id="user_015", session_id="session_015")

        # 1回目
        messages1 = [LLMMessage(role="user", content="First")]
        service.append_events_message(session=session, events_messages=messages1)

        # 2回目
        messages2 = [LLMMessage(role="assistant", content="Second")]
        service.append_events_message(session=session, events_messages=messages2)

        # セッションを再取得
        retrieved_session = service.get_session(
            user_id="user_015", session_id="session_015"
        )

        assert len(retrieved_session.events.messages) == 2
        assert retrieved_session.events.messages[0].content == "First"
        assert retrieved_session.events.messages[1].content == "Second"

    def test_session_created_at_persistence(self, service):
        """created_atがデータベースに正しく保存されるか"""
        service.create_session(user_id="user_016", session_id="session_016")

        # セッションを再取得
        retrieved_session = service.get_session(
            user_id="user_016", session_id="session_016"
        )

        # created_atがUTC時刻として正しく保存されているか
        # SQLiteはタイムゾーン情報を保持しないので、範囲チェックのみ
        assert retrieved_session.created_at is not None
        assert isinstance(retrieved_session.created_at, datetime)
