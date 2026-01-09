from typing import Union
from ...agents import AgentBase
from ...workers import WorkerBase
from ..sessions import SessionServiceBase
from ...type.agent.agent_enum import AgentSendOutput


class Runner:
    """Runnerクラス"""

    agent: Union[AgentBase, WorkerBase]
    session_service: SessionServiceBase
    memory_service = None
    artifact_service = None

    def __init__(
        self,
        *,
        agent: Union[AgentBase, WorkerBase],
        session_service: SessionServiceBase,
        artifact_service=None,
    ):
        self.agent = agent
        self.session_service = session_service
        self.artifact_service = artifact_service

    def run(
        self,
        *,
        user_id: str,
        session_id: str,
        input: str,
        **kwargs,
    ) -> AgentSendOutput:
        """
        エージェントを実行する

        Args:
            user_id (str): ユーザーID
            session_id (str): セッションID
            input (str): エージェントへの入力
        Returns:
            output: エージェントの出力
        """
        # セッションを取得または作成
        session = self.session_service.get_session(
            user_id=user_id,
            session_id=session_id,
        )
        if not session:
            session = self.session_service.create_session(
                user_id=user_id,
                session_id=session_id,
            )

        # エージェントに入力を送信し、出力を取得
        output = self.agent.run(
            session=session,
            input=input,
            **kwargs,
        )
        # イベントメッセージをセッションに追加
        self.session_service.append_events_message(
            session=session,
            events_messages=output.events_messages,
        )

        # セッションの状態を保存
        context = output.context or {}
        state_delta = context.get("session_state", {})
        if state_delta:
            self.session_service.apply_state_delta(
                session=session,
                delta=state_delta,
            )

        return output
