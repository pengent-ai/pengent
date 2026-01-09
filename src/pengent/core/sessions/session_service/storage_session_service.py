import json
from typing import Optional, Any, List
import uuid
import os

from .session_service_base import SessionServiceBase
from ....errors.already_exists_error import AlreadyExistsError
from ..session import Session
from ...message_memory.history_message_memory import HistoryMessageMemory
from ....utility.storage import StorageBase, LocalStorage

from ....type.llm.llm_message import LLMMessage


class StorageSessionService(SessionServiceBase):
    """
    Redisを使用したセッションサービスの実装
    """

    def __init__(self, storage: StorageBase = None):
        # Redisクライアントの初期化
        if storage:
            self.storage = storage
        else:
            # デフォルトのファイルストレージを使用
            self.storage = LocalStorage(bucket_name="session")

    def get_storage(self):
        """ファイルディレクトリを取得"""
        return self.storage

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

        session_data = {
            "session_id": _session.session_id,
            "user_id": _session.user_id,
            "state": json.dumps(_session.state),
            "events": json.dumps(_session.events.to_dict()),
            "created_at": _session.created_at.isoformat(),
            "last_updated_time": str(_session.last_updated_time),
        }
        self.storage.upload_bytes(
            data=json.dumps(session_data).encode("utf-8"),
            object_name=f"session/{user_id}/{_session.session_id}.json",
        )
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
        file_path = f"session/{user_id}/{session_id}.json"
        if not self.storage.exists_file(file_path):
            return None

        session_data = self.storage.read_json(file_path)
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
        sessions = []
        prefix = f"session/{user_id}/"
        all_files = self.storage.list_files(prefix=prefix)
        for file_path in all_files:
            session_id = os.path.splitext(os.path.basename(file_path))[0]
            session = self._get_session_impl(
                user_id=user_id,
                session_id=session_id,
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
        # セッションが存在っしない婆は何もしない
        file_path = f"session/{user_id}/{session_id}.json"
        if self.storage.exists_file(file_path):
            self.storage.delete_file(file_path)

    def append_events_message(
        self, session: Session, events_messages: List[LLMMessage]
    ):
        for msg in events_messages:
            session.events.add_message(msg)

        file_path = f"session/{session.user_id}/{session.session_id}.json"
        session_data = self.storage.read_json(file_path)
        session_data["events"] = json.dumps(session.events.to_dict())
        self.storage.upload_bytes(
            data=json.dumps(session_data).encode("utf-8"), object_name=file_path
        )

    def apply_state_delta(self, session: Session, delta: dict):
        if not hasattr(session, "state") or session.state is None:
            session.state = {}

        file_path = f"session/{session.user_id}/{session.session_id}.json"
        session_data: dict = self.storage.read_json(file_path)
        session_state: dict = json.loads(session_data.get("state", "{}"))
        self._deep_merge(session_state, delta)
        session_data["state"] = json.dumps(session_state)
        self.storage.upload_bytes(
            data=json.dumps(session_data).encode("utf-8"), object_name=file_path
        )
