from typing import Optional, Any
import uuid


from .session_service_base import SessionServiceBase
from ....errors.already_exists_error import AlreadyExistsError
from ..session import Session


class InMemorySessionService(SessionServiceBase):
    """
    インメモリセッションサービスの実装
    """

    def __init__(self):
        # UserIDとSessionIDの組み合わせをキーとしたセッションの辞書
        self.sessions: dict[str, dict[str, Session]] = {}

    def create_session(
        self,
        *,  # キーワード専用引数
        user_id: str,
        session_id: str,
        state: Optional[dict] = None,
    ):
        return self._create_session_impl(
            user_id=user_id,
            session_id=session_id,
            state=state,
        )

    def _create_session_impl(
        self,
        *,
        user_id: str,
        state: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Session:
        if session_id and self._get_session_impl(
            user_id=user_id, session_id=session_id
        ):
            raise AlreadyExistsError(f"Session with id {session_id} already exists.")

        _session = Session(
            session_id=session_id or uuid.uuid4().hex,
            user_id=user_id,
            state=state or {},
        )
        if user_id not in self.sessions:
            self.sessions[user_id] = {}
        self.sessions[user_id][_session.session_id] = _session
        return _session

    def get_session(
        self,
        *,
        user_id: str,
        session_id: str,
    ) -> Optional[Session]:
        return self._get_session_impl(
            user_id=user_id,
            session_id=session_id,
        )

    def _get_session_impl(
        self,
        *,
        user_id: str,
        session_id: str,
    ) -> Optional[Session]:
        user_sessions = self.sessions.get(user_id)
        if not user_sessions:
            return None

        return user_sessions.get(session_id)

    def list_sessions(
        self,
        *,
        user_id: str,
    ) -> list[Session]:
        user_sessions = self.sessions.get(user_id)
        if not user_sessions:
            return []
        return list(user_sessions.values())

    def delete_session(
        self,
        *,
        user_id: str,
        session_id: str,
    ):
        user_sessions = self.sessions.get(user_id)
        if not user_sessions or session_id not in user_sessions:
            return  # セッションが存在しない場合は何もしない

        del user_sessions[session_id]
        if not user_sessions:
            # ユーザーに関連するセッションがなくなった場合
            # ユーザーエントリを削除
            del self.sessions[user_id]
