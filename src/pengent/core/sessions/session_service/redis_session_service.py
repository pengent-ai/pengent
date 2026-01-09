import json
from typing import Optional, Any, List
import uuid
import redis
import os

from .session_service_base import SessionServiceBase
from ....errors.already_exists_error import AlreadyExistsError
from ..session import Session
from ...message_memory.history_message_memory import HistoryMessageMemory
from ....type.llm.llm_message import LLMMessage

# SESSION_KEY_PREFIX = "session:{user_id}:{session_id}"


class RedisSessionService(SessionServiceBase):
    """
    Redisを使用したセッションサービスの実装
    """

    def __init__(self, redis_client: redis.Redis = None):
        # Redisクライアントの初期化
        if redis_client:
            self.redis_client = redis_client
            return

        self.redis_client = redis.Redis(
            host=os.environ.get("REDIS_HOST", "localhost"),
            port=os.environ.get("REDIS_PORT", 6379),
            password=os.environ.get("REDIS_PASSWORD", "change_me"),
            decode_responses=True,  # 文字列としてデコード
        )

    def get_client(self):
        """Redisクライアントを取得"""
        return self.redis_client

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

        key = f"session:{user_id}:{_session.session_id}"
        session_data = {
            "session_id": _session.session_id,
            "user_id": _session.user_id,
            "state": json.dumps(_session.state),
            "events": json.dumps(_session.events.to_dict()),
            "created_at": _session.created_at.isoformat(),
            "last_updated_time": str(_session.last_updated_time),
        }
        self.redis_client.hset(key, mapping=session_data)
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
        key = f"session:{user_id}:{session_id}"
        session_data = self.redis_client.hgetall(key)
        if not session_data:
            return None

        state = {}
        if "state" in session_data and session_data["state"]:
            state = json.loads(session_data["state"])

        events_dict = {}
        if "events" in session_data and session_data["events"]:
            events_dict = json.loads(session_data["events"])
            events = HistoryMessageMemory.from_dict(events_dict)
        else:
            events = HistoryMessageMemory()

        return Session(
            session_id=session_data["session_id"],
            user_id=session_data["user_id"],
            state=state,
            events=events,
            created_at=session_data["created_at"],
            last_updated_time=float(session_data["last_updated_time"]),
        )

    def list_sessions(
        self,
        *,
        user_id: str,
    ) -> list[Session]:
        pattern = f"session:{user_id}:*"
        keys = self.redis_client.keys(pattern)
        sessions = []
        for key in keys:
            session_data = self.redis_client.hgetall(key)
            if session_data:
                session = self._get_session_impl(
                    user_id=user_id, session_id=session_data["session_id"]
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
        key = f"session:{user_id}:{session_id}"
        self.redis_client.delete(key)

    def append_events_message(
        self, session: Session, events_messages: List[LLMMessage]
    ):
        for msg in events_messages:
            session.events.add_message(msg)

        key = f"session:{session.user_id}:{session.session_id}"
        self.redis_client.hset(key, "events", json.dumps(session.events.to_dict()))

    def apply_state_delta(self, session: Session, delta: dict):
        if not hasattr(session, "state") or session.state is None:
            session.state = {}

        self._deep_merge(session.state, delta)
        key = f"session:{session.user_id}:{session.session_id}"
        self.redis_client.hset(key, "state", json.dumps(session.state))
