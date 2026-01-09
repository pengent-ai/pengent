from typing import Optional, List
from ..session import Session
from ....type.llm.llm_message import LLMMessage


class SessionServiceBase:
    """
    セッションサービスの基底クラス
    """

    def create_session(
        self,
        *,  # キーワード専用引数
        user_id: str,
        session_id: str,
        state: Optional[dict] = None,
    ):
        """
        セッションを作成するメソッド

        Args:
            user_id(str): ユーザーID
            session_id(str): セッションID
            state(Optional[dict]): セッションの初期状態
        """
        raise NotImplementedError("create_session method not implemented.")

    def get_session(
        self,
        *,
        user_id: str,
        session_id: str,
    ) -> Optional[Session]:
        """
        セッションを取得するメソッド

        Args:
            user_id(str): ユーザーID
            session_id(str): セッションID

        """
        raise NotImplementedError("get_session method not implemented.")

    def list_sessions(
        self,
        *,
        user_id: str,
    ) -> list[Session]:
        """
        ユーザーに関連する全てのセッションをリストするメソッド

        Args:
            user_id(str): ユーザーID
        Returns:
            list[Session]: Sessionオブジェクトのリスト
        """
        raise NotImplementedError("list_sessions method not implemented.")

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
        raise NotImplementedError("delete_session method not implemented.")

    def append_events_message(
        self, session: Session, events_messages: List[LLMMessage]
    ):
        """
        セッションを保存するメソッド

        Args:
            Session(Session): 保存するセッションオブジェクト
        """
        for msg in events_messages:
            session.events.add_message(msg)

    def apply_state_delta(self, session: Session, delta: dict):
        """
        セッション状態に差分を適用する
        """
        if not hasattr(session, "state") or session.state is None:
            session.state = {}

        self._deep_merge(session.state, delta)

    @classmethod
    def _deep_merge(cls, base: dict, delta: dict):
        for k, v in delta.items():
            if v is None:
                base.pop(k, None)
                continue

            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                cls._deep_merge(base[k], v)
            else:
                base[k] = v
