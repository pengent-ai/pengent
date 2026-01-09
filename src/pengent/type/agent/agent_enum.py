from copy import deepcopy
from typing import List, Union, Optional
from dataclasses import dataclass, field
from ...core.sessions import Session
from ..llm.llm_message import LLMMessageContent, LLMMessage
from ...core.artifacts.artifact_service import (
    ArtifactServiceBase,
    ExecutionArtifactService,
)
from ...core.artifacts.artifact import ArtifactBase


@dataclass
class AgentSendInput:
    """
    AgentInputクラス(エージェントの入力データ)
    エージェントが送信する入力データを提供します。
    """

    content: Optional[Union[str, List[LLMMessageContent]]] = None
    summary: Optional[str] = None  # 要約
    prior_info: Optional[dict] = None  # 事前情報
    template: Optional[str] = None  # テンプレート名
    state: Optional[dict] = None  # セッション状態

    def to_dict(self) -> dict:
        """
        エージェントの入力データを辞書形式に変換します。
        """
        data = {
            "content": self.content,
            "summary": self.summary,
            "prior_info": self.prior_info,
            "template": self.template,
        }
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> "AgentSendInput":
        return cls(**data)

    def set_session(self, session: Session):
        """セッション状態をコピーするメソッド"""
        self.state = deepcopy(session.state) if session.state else {}


@dataclass
class AgentSendOutput:
    """
    AgentOutputクラス(エージェントの出力データ)
    エージェントが生成する出力データを提供します。

    Notes:
        - contextの内容
            - `state_delta`: セッション状態の変更点を含む辞書
    """

    message: Optional[str] = None
    context: Optional[dict[str, any]] = field(default_factory=dict)
    events_messages: Optional[List[LLMMessage]] = None

    def set_context(self, key, value: any):
        """コンテキストを設定するメソッド"""
        if self.context is None:
            self.context = {}
        self.context[key] = value

    @classmethod
    def from_dict(cls, data: dict) -> "AgentSendOutput":
        return cls(
            message=data.get("message"),
            context=data.get("context ", {}),
            events_messages=LLMMessage.from_dict_messages(
                data.get("events_messages", [])
            ),
        )

    def to_dict(self) -> dict:
        """
        エージェントの出力データを辞書形式に変換します。
        """
        data = {
            "message": self.message,
            "context ": self.context,
            "events_messages": LLMMessage.to_dict_messages(self.events_messages)
            if self.events_messages
            else None,
        }
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class ExecutionContext:
    """
    実行中のコンテキストクラス

    Notes:
        - state は読み取り専用
        - 変更が必要な場合は state_delta としてResponse.contextに返す
    """

    session_id: str  # セッションID
    user_id: str  # ユーザーID
    state: Optional[dict]  # セッション状態
    _state_delta: dict = field(default_factory=dict)
    _artifact_service: Optional[ExecutionArtifactService] = field(default=None)

    @classmethod
    def create(
        cls, session: Session, artifact_service: ArtifactServiceBase = None
    ) -> "ExecutionContext":
        """SessionオブジェクトからExecutionContextを作成するクラスメソッド"""
        _artifact_service = None
        if artifact_service:
            _artifact_service = ExecutionArtifactService(
                base=artifact_service,
                user_id=session.user_id,
                session_id=session.session_id,
            )

        return cls(
            session_id=session.session_id,
            user_id=session.user_id,
            state=deepcopy(session.state) if session.state else {},
            _state_delta={},
            _artifact_service=_artifact_service,
        )

    def get_state_delta(self) -> Optional[dict]:
        """状態の変更点を取得するメソッド"""
        return self._state_delta

    def set_state_delta(self, key: str, value: any):
        """状態の変更点を設定するメソッド"""
        self._state_delta[key] = value

    def update_state_delta(self, delta: dict):
        """状態の変更点を更新するメソッド"""
        self._state_delta.update(delta)

    def save_artifact(
        self,
        filename: str,
        artifact: ArtifactBase,
        custom_meta: dict = None,
    ) -> int:
        """アーティファクトを保存するメソッド"""
        if not self._artifact_service:
            return None
        return self._artifact_service.save(
            file_name=filename,
            artifact=artifact,
            custom_meta=custom_meta,
        )

    def load_artifact(
        self,
        filename: str,
        version: int = None,
    ) -> Optional[ArtifactBase]:
        """アーティファクトを読み込むメソッド"""
        if not self._artifact_service:
            return None
        return self._artifact_service.load(
            file_name=filename,
            version=version,
        )
