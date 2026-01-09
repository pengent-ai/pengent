from typing import Optional, Any
from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Session as DBSession

from .session_service_base import SessionServiceBase
from ....errors.already_exists_error import AlreadyExistsError
from ..session import Session
from ....db.models.session_orm import SessionORM
from ....db.models.messages_orm import MessageORM
from ...message_memory.history_message_memory import HistoryMessageMemory
from ....type.llm.llm_message import LLMMessage, LLMMessageRole


class DatabaseSessionService(SessionServiceBase):
    """
    データベースセッションサービスの実装
    """

    def __init__(self, db=None):
        from ....db.base import Database

        if db:
            self.db = db
        else:
            self.db = Database.create_database()

    def create_session(
        self,
        *,  # キーワード専用引数
        user_id: str,
        session_id: str,
        state: Optional[dict] = None,
    ):
        with self.db.get_session() as db_session:
            return self._create_session_impl(
                db_session=db_session,
                user_id=user_id,
                session_id=session_id,
                state=state,
            )

    def _create_session_impl(
        self,
        *,
        db_session: DBSession,
        user_id: str,
        state: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Session:
        if session_id and self._is_session_exists(
            db_session=db_session,
            user_id=user_id,
            session_id=session_id,
        ):
            raise AlreadyExistsError(f"Session with id {session_id} already exists.")

        _session = Session(
            session_id=session_id or uuid.uuid4().hex,
            user_id=user_id,
            state=state or {},
        )
        # セッションをDBに保存
        session_orm = SessionORM(
            session_id=_session.session_id,
            user_id=_session.user_id,
            state=_session.state,
            events_max_messages=_session.events.max_messages,
            messages_type=_session.events._type,
            created_at=_session.created_at,
            last_updated_time=_session.last_updated_time,
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(session_orm)
        db_session.commit()
        return _session

    def get_session(
        self,
        *,
        user_id: str,
        session_id: str,
    ) -> Optional[Session]:
        with self.db.get_session() as db_session:
            return self._get_session_impl(
                db_session=db_session,
                user_id=user_id,
                session_id=session_id,
            )

    def _get_session_impl(
        self,
        *,
        db_session: DBSession,
        user_id: str,
        session_id: str,
    ) -> Optional[Session]:
        # セッションをDBから取得
        session_orm = (
            db_session.query(SessionORM)
            .filter_by(user_id=user_id, session_id=session_id)
            .first()
        )
        if not session_orm:
            return None
        # SessionORMからSessionオブジェクトを作成して返す
        events = HistoryMessageMemory(
            max_messages=session_orm.events_max_messages,
        )
        # イベントメッセージを復元
        messages_orm = (
            db_session.query(MessageORM)
            .filter_by(user_id=user_id, session_id=session_id)
            .all()
        )

        for message_orm in messages_orm:
            llm_message = LLMMessage(
                role=LLMMessageRole(message_orm.role),
                content=message_orm.content,
                tool_call_id=message_orm.tool_call_id,
                tool_calls=message_orm.tool_calls or None,
                meta_data=message_orm.meta_data or None,
            )
            events.add_message(llm_message)

        session = Session(
            session_id=session_orm.session_id,
            user_id=session_orm.user_id,
            state=session_orm.state,
            created_at=session_orm.created_at,
            events=events,
            last_updated_time=session_orm.last_updated_time,
        )
        return session

    def _is_session_exists(
        self,
        *,
        db_session: DBSession,
        user_id: str,
        session_id: str,
    ) -> bool:
        session_orm = (
            db_session.query(SessionORM)
            .filter_by(user_id=user_id, session_id=session_id)
            .first()
        )
        return session_orm is not None

    def list_sessions(
        self,
        *,
        user_id: str,
    ) -> list[Session]:
        """
        ユーザーに関連する全てのセッションをリストするメソッド

        Notes:
            - DBセッションは呼び出し元で管理する必要があります
            - Eventsメッセージは含まれませんので注意が必要です
        """
        with self.db.get_session() as db_session:
            session_orms = db_session.query(SessionORM).filter_by(user_id=user_id).all()
            sessions = []
            for session_orm in session_orms:
                session = self._get_session_impl(
                    db_session=db_session,
                    user_id=user_id,
                    session_id=session_orm.session_id,
                )
                if session:
                    sessions.append(session)
            return sessions

    def delete_session(
        self,
        *,
        user_id: str,
        session_id: str,
    ):
        """
        セッションを削除するメソッド

        Args:
            user_id(str): ユーザーID
            session_id(str): セッションID
        """
        with self.db.get_session() as db_session:
            self._delete_session_impl(
                db_session=db_session,
                user_id=user_id,
                session_id=session_id,
            )

    def _delete_session_impl(
        self,
        *,
        db_session: DBSession,
        user_id: str,
        session_id: str,
    ):
        # セッションをDBから削除
        session_orm = (
            db_session.query(SessionORM)
            .filter_by(user_id=user_id, session_id=session_id)
            .first()
        )
        if session_orm:
            db_session.delete(session_orm)
            # 関連するメッセージも削除
            db_session.query(MessageORM).filter_by(
                user_id=user_id, session_id=session_id
            ).delete()
            db_session.commit()

    def append_events_message(
        self,
        *,
        session: Session,
        events_messages: list[LLMMessage],
    ):
        """
        セッションにイベントメッセージを追加するメソッド

        Args:
            session(Session): セッションオブジェクト
            events_messages(list[LLMMessage]): 追加するイベントメッセージ
        """
        with self.db.get_session() as db_session:
            for llm_message in events_messages:
                message_orm = MessageORM(
                    session_id=session.session_id,
                    user_id=session.user_id,
                    role=llm_message.role,
                    content=llm_message.content,
                    tool_call_id=llm_message.tool_call_id,
                    tool_calls=llm_message.tool_calls,
                    meta_data=llm_message.meta_data,
                    created_at=datetime.now(timezone.utc),
                )
                db_session.add(message_orm)
            # セッションのlast_updated_timeを更新
            session_orm = (
                db_session.query(SessionORM)
                .filter_by(user_id=session.user_id, session_id=session.session_id)
                .first()
            )
            session.last_updated_time = datetime.now(timezone.utc).timestamp()
            if session_orm:
                session_orm.updated_at = datetime.now(timezone.utc)
                session_orm.last_updated_time = session.last_updated_time
            db_session.commit()

    def apply_state_delta(
        self,
        *,
        session: Session,
        delta: dict,
    ):
        """
        セッションの状態にデルタを適用するメソッド

        Args:
            session(Session): セッションオブジェクト
            delta(dict): 適用する状態のデルタ
        """
        with self.db.get_session() as db_session:
            # セッションの状態を更新
            session_orm = (
                db_session.query(SessionORM)
                .filter_by(user_id=session.user_id, session_id=session.session_id)
                .first()
            )
            if not session_orm:
                raise ValueError("Session not found")

            base_state = session_orm.state or {}

            self._deep_merge(base_state, delta)
            # DBへ反映
            now = datetime.now(timezone.utc)
            session_orm.state = base_state
            session_orm.last_updated_time = now.timestamp()
            session_orm.updated_at = now
            db_session.commit()

            # メモリ側の session にも同期
            session.state = base_state
            session.last_updated_time = session_orm.last_updated_time
