import uuid
import json
from datetime import datetime

from typing import Union, Optional
from ..policies.polices.policy_base import PolicyBase


from ..core.sessions.session import Session
from ..type.llm.llm_message import LLMMessage, LLMMessageTool
from ..type.llm.llm_response import LLMResponse
from ..type.agent.agent_enum import (
    AgentSendInput,
    AgentSendOutput,
    ExecutionContext,
)


from ..tools import ToolUnion, ToolBase, ToolUtils


class WorkerBase:
    """
    全ワーカーの共通基底クラス
    """

    def __init__(
        self,
        name: str,
        policy: PolicyBase = None,
        params: dict = None,
        tools: list[ToolUnion] = None,
        logger=None,
    ):
        self.name = name
        self.policy = policy
        self.params = params if params else {}
        if logger:
            self.logger = logger
        else:
            from ..lib import get_logger

            self.logger = get_logger()

        self.tools: list[ToolUnion] = tools if tools else []
        self._tool_map: dict[str, ToolBase] = {}

        # コールバックを設定するメソッド
        self.message_callback = None

    def set_policy(self, policy: PolicyBase):
        """ポリシーを設定する"""
        self.policy = policy

    def run(
        self,
        session: Session,
        ctx: Optional[ExecutionContext] = None,
        input: Union[str, dict, AgentSendInput] = None,
        **kwargs,
    ) -> AgentSendOutput:
        """ワーカーを起動するメソッド"""
        self.logger.info(f"{self.name} is Running.")

        if self.tools and not self._tool_map:
            tool_bases: list[ToolBase] = ToolUtils.normalize_tools(self.tools)
            self._tool_map = {tool.name: tool for tool in tool_bases}

        return self.send(input, session, ctx, **kwargs)

    def send(
        self,
        input: Union[str, dict, AgentSendInput] = None,
        session: Session = None,
        ctx: Optional[ExecutionContext] = None,
        **kwargs,
    ):
        """
        ワーカーにメッセージを送信するメソッド
        """
        try:
            # セッション状態の一時的なバッファ
            if session is None and ctx is not None:
                raise ValueError("Either session or ctx must be provided.")
            if session is None:
                session = Session(
                    session_id=uuid.uuid4().hex,
                    user_id=f"gestuser-{int(datetime.now().timestamp())}",
                )

            if not ctx:
                ctx = ExecutionContext.create(session=session)

            self.logger.debug(f"send message start. input: {input}")
            if input and isinstance(input, dict):
                input = AgentSendInput(**input)
            elif input and isinstance(input, str):
                input = AgentSendInput(content=input)

            # ユーザープロンプトの自動生成機能が有効か確認する
            is_make_user_prompt = self.get_value_for_kwargs(
                "is_make_user_prompt", False, **kwargs
            )

            if is_make_user_prompt:
                self.logger.debug("make user prompt.")
                text = self.make_user_prompt(**input.to_dict())
            else:
                if input.content and isinstance(input.content, str):
                    text = input.content.strip()
                elif input.content and isinstance(input.content, list):
                    for con in input.content:
                        text = con.text.strip()

            self.logger.debug(f"send message text: {text}")

            messages = []
            _message = LLMMessage.create_user_message(text)
            messages.append(_message)
            response = self.action_request(
                messages=session.events.get() + messages,
                context=ctx,
            )
            return self.receive_message(session, response, messages, context=ctx)

        except Exception as e:
            self.logger.exception(f"send message Error: {e}")
            raise e
        finally:
            self.logger.debug("send message end.")

    def receive_message(
        self,
        session: Session,
        response: LLMResponse,
        messages: list[LLMMessage],
        *,
        context: Optional[ExecutionContext] = None,
    ):
        """
        エージェントが受信したメッセージを処理するメソッド
        """
        # ツールが呼ばれていないか確認する
        tools = response.get_tools()
        if tools:
            response = self.handle_tools_call(session, messages, tools, context=context)

        # メッセージを確認する
        if not response.is_message():
            # メッセージがない場合は、エラーを返す
            self.logger.error(f"receive_message Error: {response}")
            raise ValueError("no message.")

        output = AgentSendOutput(message=response.get_message())

        _message = LLMMessage.create_assistant_message(output.message)
        messages.append(_message)

        self.logger.debug(f"receive_message end. {output}")
        return self.handler_message(messages, output, context=context)

    def _exec_tool_call_worker_response(
        self,
        session: Session,
        result: Union[str, dict, list],
        messages: list[LLMMessage],
        tool: LLMMessageTool,
        *,
        context: Optional[ExecutionContext] = None,
    ):
        if isinstance(result, list) or isinstance(result, dict):
            result = json.dumps(result)
        # ツールコールの結果メッセージを作成する
        _message = LLMMessage.create_tools_result(tool_call_id=tool.id, content=result)
        messages.append(_message)
        response = self.action_request(
            messages=session.events.get() + messages,
            context=context,
        )
        return response

    def _exec_tool_call(
        self,
        session: Session,
        messages: list[LLMMessage],
        tool: LLMMessageTool,
        *,
        context: Optional[ExecutionContext] = None,
    ):
        """
        ツールコールを実行するメソッド
        """
        self.logger.debug(f"tool: {tool.function.name} {tool.function.arguments}")

        # ツールを実行するためのMapを持つ
        name = tool.function.name
        tool_base = self._tool_map.get(name)
        if not tool_base:
            result = json.dumps({"error": f"Tool Not Found in Agent: {name}"})
        else:
            result = ToolUtils.execute_tool(
                tool_base,
                tool.function.arguments,
                context=context,
            )
        return self._exec_tool_call_worker_response(
            session, result, messages, tool, context=context
        )

    def handle_tools_call(
        self,
        session: Session,
        messages: list[LLMMessage],
        tools: list[LLMMessageTool],
        *,
        context: Optional[ExecutionContext] = None,
    ):
        self.logger.debug(f"handle_tools_call receive tools: {tools}")

        # ワーカーからのツールコールリクエストを処理する
        _message = LLMMessage.create_tools_call(tools)
        messages.append(_message)

        for tool in tools:
            response = self._exec_tool_call(session, messages, tool, context=context)

        return response

    def handler_message(
        self,
        messages: list[LLMMessage],
        output: AgentSendOutput,
        *,
        context: Optional[ExecutionContext] = None,
    ) -> AgentSendOutput:
        """
        エージェントからの応答を処理するメソッド
        """
        output.events_messages = messages
        self._output = output

        if context.get_state_delta():
            output.set_context("state_delta", context.get_state_delta())

        if self.message_callback:
            # メッセージコールバックが設定されている場合は呼び出す
            self.logger.debug("call message callback.")
            self.message_callback(messages, output)

        return output

    def action_request(
        self,
        messages: list[LLMMessage],
        *,
        context: Optional[ExecutionContext] = None,
    ) -> LLMResponse:
        """
        メッセージを送信して、アクションを実行する
        """
        raise NotImplementedError("action_request is not implemented in WorkerBase")

    # ----------------------------
    # params
    def get_value_for_kwargs(self, key, default=None, **kwargs) -> any:
        return kwargs.get(key, self.params.get(key, default))

    # ----------------------------
    # Agentのオプション設定項目

    @property
    def is_make_user_prompt(self) -> bool:
        """ユーザープロンプトを自動生成するかどうか"""
        return self.params.get("is_make_user_prompt", False)

    @is_make_user_prompt.setter
    def is_make_user_prompt(self, value: bool):
        self.params["is_make_user_prompt"] = value

    # -----------------------------
    # user prompt

    def make_user_prompt(self, **kwargs) -> str:
        """ユーザープロンプトを自動生成するメソッド

        Notes:
            - 現在は使用されないことを想定しています。
        """
        user_prompt = ""

        content = kwargs.get("content", None)
        if content:
            user_prompt += f"{content}"

        return user_prompt
