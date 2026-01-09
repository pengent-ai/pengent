import uuid
import time
import json
from datetime import datetime

from typing import Union, Optional
from ..llm.llm_client_base import LLMClientBase

# メッセージメモリ及びタスクの状態管理、ツール管理をするためのモジュール
from ..core.sessions.session import Session
from ..type.llm.llm_message import LLMMessage, LLMMessageTool
from ..type.llm.llm_response import LLMResponse
from ..type.agent.agent_enum import (
    AgentSendInput,
    AgentSendOutput,
    ExecutionContext,
)

from ..tools import ToolUnion, ToolBase, ToolUtils


from ..lib.common import strip_json_fence


class AgentBase:
    """
    全エージェントの共通基底クラス(personal)
    """

    def __init__(
        self,
        name: str,
        llm_client: LLMClientBase = None,
        params: dict = None,
        tools: list[ToolUnion] = None,
        logger=None,
    ):
        """
        コンストラクタ

        Args:
            name (str): エージェント名
            llm_client (LLMClientBase, optional): LLMクライアント
            params (dict, optional): エージェントパラメータ
            tools (list[ToolUnion], optional):ツールリスト.
            logger (optional): ロガーインスタンス.
        """
        self.name = name
        self.llm_client = llm_client
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

    def set_llm_client(self, llm_client: LLMClientBase):
        """LLMクライアントを設定する"""
        self.llm_client = llm_client

    def add_tool(self, tool: ToolUnion):
        """エージェントにツールを追加するメソッド"""
        if not self.tools:
            self.tools = []
        self.tools.append(tool)

    def set_system_prompt(self, system_prompt: str):
        """システムプロンプトを設定する(上書き)

        Args:
            system_prompt (str): システムプロンプト
        """
        self.params["system_prompt"] = system_prompt

    # ----------------------------
    # Main Method

    def run(
        self,
        session: Session,
        input: Union[str, dict, AgentSendInput] = None,
        ctx: Optional[ExecutionContext] = None,
        **kwargs,
    ) -> AgentSendOutput:
        """
        エージェントを起動する
        """
        self.logger.info(f"{self.name} is Running.")

        # LLMクライアントにツールを設定する
        # (_tool_mapがあればキャッシュされているのでスキップ)
        if self.tools and not self._tool_map:
            tool_bases: list[ToolBase] = ToolUtils.normalize_tools(self.tools)
            self._tool_map = {tool.name: tool for tool in tool_bases}
            self.logger.debug("set tools to llm client.")
            self.llm_client.tools = [t.dump() for t in tool_bases]

        # LLMクライアントにシステムプロンプトを指定する
        self.llm_client.system_prompt = self.system_prompt

        return self.send(input, session, ctx, **kwargs)

    def send(
        self,
        input: Union[str, dict, AgentSendInput] = None,
        session: Session = None,
        ctx: Optional[ExecutionContext] = None,
        **kwargs,
    ):
        """
        エージェントにメッセージを送信するメソッド
        """
        try:
            if session is None and ctx is not None:
                raise ValueError("Either session or ctx must be provided.")
            if session is None:
                # セッションが存在しない婆は作成する
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
            input.set_session(session)

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

            # メッセージの送信処理について
            messages = []
            _message = LLMMessage.create_user_message(text)
            messages.append(_message)
            response = self.llm_client.request(messages=session.events.get() + messages)
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

        response, output = self._with_retry(session, response, messages)
        _message = LLMMessage.create_assistant_message(output.message)
        messages.append(_message)

        self.logger.debug(f"receive_message end. {output}")
        return self.handler_message(messages, output, context=context)

    def _register_tools_call(
        self, messages: list[LLMMessage], tools: list[LLMMessageTool]
    ):
        """Functionsコールをメッセージに登録するメソッド"""
        _message = LLMMessage.create_tools_call(tools)
        messages.append(_message)

    def _exec_tool_call_response(
        self,
        session: Session,
        result: Union[str, dict, list],
        messages: list[LLMMessage],
        tool: LLMMessageTool,
    ):
        if isinstance(result, list) or isinstance(result, dict):
            result = json.dumps(result)
        _message = LLMMessage.create_tools_result(tool_call_id=tool.id, content=result)
        messages.append(_message)  #
        response = self.llm_client.request(messages=session.events.get() + messages)
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
        return self._exec_tool_call_response(session, result, messages, tool)

    def handle_tools_call(
        self,
        session: Session,
        messages: list[LLMMessage],
        tools: list[LLMMessageTool],
        *,
        context: Optional[ExecutionContext] = None,
    ):
        self.logger.debug(f"handle_tools_call receive tools: {tools}")
        self._register_tools_call(messages, tools)
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

    def _with_retry(
        self,
        session: Session,
        response: LLMResponse,
        messages: list[LLMMessage],
    ) -> tuple[LLMResponse, AgentSendOutput]:
        """LLMメッセージリクエストをパース(リトライ/再送信)するための中間メソッド"""
        # リトライの回数とリトライ間隔
        max_retries = self.params.get("retry_max_count", 3)
        retry_delay_sec = self.params.get("retry_delay_sec", 10)

        for attempt in range(max_retries):
            try:
                output = self._parse_response_content(response)
                return response, output  # 成功
            except Exception as e:
                error_detail = str(e)
                self.logger.error(
                    f"Parse failed on attempt {attempt + 1}: {error_detail}"
                )
                messages.append(
                    LLMMessage.create_assistant_message(response.get_message())
                )
                messages.append(
                    LLMMessage.create_user_message(
                        content=(
                            "**Failed to parse the response.**\n"
                            "Please make sure the output format is correct "
                            "and includes all required keys.\n"
                            f"(Detail: {error_detail})"
                        )
                    )
                )
                if attempt < max_retries - 1:
                    time.sleep(retry_delay_sec)
                    response = self.llm_client.request(
                        messages=session.events.get() + messages
                    )
                else:
                    raise ValueError(
                        f"Parsing failed after {max_retries} attempts. "
                        f"Last error: {error_detail}"
                    ) from e

    def _parse_response_content(self, response: LLMResponse) -> AgentSendOutput:
        """パースを実行するメソッド"""
        self.logger.debug("_parse_response_content start.")
        self.logger.debug(
            f"format: {self.format} is_contents_type: {self.is_contents_type}"
        )
        content_text = response.get_message()
        if self.is_contents_type:
            # 先頭に出力タイプ
            lines = content_text.splitlines()
            self.logger.info(
                f"contents_type(Head 1 Line):{lines[0].strip() if lines else ''}"
            )
            content_text = "\n".join(lines[1:]) if len(lines) > 1 else ""

        self.logger.debug(f"content_text:\n{content_text}")

        if self.params.get("callback_parse"):  # 独自のパース関数で実行する場合
            self.logger.debug("Using custom call_parse method.")
            return self.params["callback_parse"](content_text)

        # 通常パースを実行する
        if self.format == "application/json":
            self.logger.debug("Parsing as JSON.")
            content_text = strip_json_fence(content_text)
            content_json = self.llm_client.parse_json(content_text)
            output = AgentSendOutput()
            output.message = content_json.get("message", "JSON Response No Message")
            output.set_context("json", content_json)
            return output
        else:
            self.logger.debug("no parse text.")
            return AgentSendOutput(message=content_text)

    # ----------------------------
    # params

    @property
    def format(self) -> str:
        return self.params.get("format", "text/plain")

    @format.setter
    def format(self, value: str):
        self.params["format"] = value

    @property
    def call_agents(self) -> list[dict]:
        """呼び出せる関数・ツールのリスト"""
        return self.params.get("call_agents", None)

    @call_agents.setter
    def call_agents(self, value: list[dict]):
        self.params["call_agents"] = value

    def dump_call_agents(self):
        """呼び出すことのできるエージェントJSON形式でダンプするメソッド(プロンプト用)"""
        return json.dumps(self.call_agents, indent=2, ensure_ascii=False)

    @property
    def system_prompt(self) -> str:
        """システムプロンプトを取得する

        Notes:
            - paramsにsystem_promptが設定されていれば、優先して使用する。
            - それ以外の場合は、make_system_promptメソッドを使用して生成する。
        """
        if self.params.get("system_prompt", None):
            return self.params["system_prompt"]
        else:
            return self.make_system_prompt()

    def update_param(self, key: str, value: any):
        """
        エージェントのパラメータを更新するメソッド

        Parameters:
            key (str): パラメータのキー
            value (any): パラメータの値
        """
        self.params[key] = value

    def clear_param(self, key: str):
        """
        エージェントのパラメータを更新するメソッド

        Parameters:
            key (str): パラメータのキー
        """
        if key in self.params:
            del self.params[key]

    def get_value_for_session_stat(
        self, session: Session, key, default=None, **kwargs
    ) -> any:
        val = session.stat.get(key, None)
        if val:
            return val
        return kwargs.get(key, self.params.get(key, default))

    def get_value_for_kwargs(self, key, default=None, **kwargs) -> any:
        return kwargs.get(key, self.params.get(key, default))

    def get_value_for_params(
        self,
        key,
        default=None,
    ) -> any:
        return self.params.get(key, default)

    # -----------------------------
    # Agentのオプション設定項目

    @property
    def is_disable_system_pronpt(self) -> bool:
        """システムプロンプトを禁止する"""
        return self.params.get("is_disable_system_pronpt", False)

    @is_disable_system_pronpt.setter
    def is_disable_system_pronpt(self, value: bool):
        self.params["is_disable_system_pronpt"] = value

    @property
    def is_contents_type(self) -> bool:
        """受信メッセージの先頭(1行目)に出力タイプを含むかどうか"""
        return self.params.get("is_contents_type", False)

    @is_contents_type.setter
    def is_contents_type(self, value: bool):
        self.params["is_contents_type"] = value

    @property
    def is_make_user_prompt(self) -> bool:
        """ユーザープロンプトを自動生成するかどうか"""
        return self.params.get("is_make_user_prompt", False)

    @is_make_user_prompt.setter
    def is_make_user_prompt(self, value: bool):
        self.params["is_make_user_prompt"] = value

    @property
    def is_outoput_example(self) -> bool:
        """システムプロンプトに出力のサンプルを自動的に含めるかどうか
        Notes:
            - 手動でexampleを設定した場合は、is_outoput_exampleは無効となる。
        """
        return self.params.get("is_outoput_example", True)

    @is_outoput_example.setter
    def is_outoput_example(self, value: bool):
        self.params["is_outoput_example"] = value

    @property
    def is_outoput_schema(self) -> bool:
        """
        システムプロンプトに出力するJSONスキーマを含むかどうか(JSON形式)

        Notes:
            - 手動でschemaを設定した場合は、is_outoput_schemaは無効となる。
            - トークンが増えるためデフォルトではFalseに設定されている。
        """
        return self.params.get("is_outoput_schema", False)

    @is_outoput_schema.setter
    def is_outoput_schema(self, value: bool):
        self.params["is_outoput_schema"] = value

    @property
    def is_add_outoput_constraints(self) -> bool:
        """システムプロンプトに出力フォーマットにあわせた制約を自動的に含めるかどうか"""
        return self.params.get("is_add_outoput_constraints", True)

    @is_add_outoput_constraints.setter
    def is_add_outoput_constraints(self, value: bool):
        self.params["is_add_outoput_constraints"] = value

    # ----------------------------
    # system_prompt
    def make_system_prompt(self) -> str:
        """
        システムプロンプトを生成するメソッド
        """
        if self.is_disable_system_pronpt:
            return None

        system_prompt = ""

        role = self.get_value_for_params("role", "you are an assistant")
        system_prompt += f"## Role:\n{role}\n\n"

        goal = self.get_value_for_params("goal")
        if goal:
            system_prompt += "## Goal\nあなたの役割は次の通りです。\n"
            system_prompt += f"目的: {goal}\n\n"

        # 出力フォーマット
        system_prompt += "## Output\n\n"

        if self.format == "text/plain":
            system_prompt += (
                "期待される出力は自然な日本語の文章です。構造化は不要です。\n\n"
            )
        elif self.format == "application/json":
            system_prompt += "期待される出力は純粋な JSON オブジェクトです。\n"
            system_prompt += "コードブロック(``` など)は出力しないこと\n\n"
        elif self.format == "text/markdown":
            system_prompt += "期待される出力はMarkdown形式の構造化された文章です。\n"
            system_prompt += (
                "見出し(#, ##, ###など)やリスト、表、"
                "コードブロックなどを適切に使用すること。\n"
            )
            system_prompt += (
                "読みやすさと構造化を意識し、自然な日本語で記述すること。\n\n"
            )

        # 出力スキーマを出力する
        schema = self.get_value_for_params("schema", None)
        if schema:
            system_prompt += f"### Schema:\n````\n{schema}\n````\n\n"

        # 出力サンプルを出力する
        example = self.get_value_for_params("example", None)
        if example:
            system_prompt += "### Example:n"
            if self.is_contents_type:
                system_prompt += f"{self.format}\n"
            system_prompt += f"{example}\n\n"

        # 呼び出せるツール・関数を制御する
        if self.call_agents:
            system_prompt += "## Enable Calling Agents\n"
            system_prompt += "必要な時は次のエージェントを呼び出すことができます:\n"
            system_prompt += f"````\n{self.dump_call_agents()}\n````\n\n"

        # SOPに関する指示
        sop_list = []
        sop_list += self.get_value_for_params("sop", [])
        if sop_list:
            system_prompt += "## SOP (ordered)\n"
            system_prompt += "\n".join(f"- {s}" for s in sop_list) + "\n\n"

            # 実行ルールを明記(順序厳守／ブロック時の振る舞い)
            system_prompt += (
                "### 実行ルール\n"
                "- 上から順に1→2 → ... と実行すること"
                "(指示のない順番変更・スキップ・並行実行は禁止)。\n"
                "- 実行不能な場合は 理由 または不足情報(最大3つ)のみ返し、"
                "推測で進めないこと。\n"
                "- 上記に従わない出力は無効とみなし破棄する。\n\n"
            )

        # 制約に関する指示
        constraints = []
        constraints += self.get_value_for_params("constraints", [])
        if isinstance(constraints, str):
            constraints = [constraints]

        if constraints:
            constraints += [
                "**上記の指示を守れない場合は、出力は破棄され、再実行されます。**"
            ]
            system_prompt += "## Constraints:\n"
            system_prompt += (
                f"{chr(10).join([f'- {constraint}' for constraint in constraints])}\n\n"
            )

        return system_prompt

    # ----------------------------
    # user_prompt

    def make_user_prompt(self, **kwargs) -> str:
        user_prompt = ""
        content = kwargs.get("content", None)
        # 本文を出力する
        if content:
            if isinstance(content, str):
                _content = content.strip()
            elif isinstance(content, list):
                for con in content:
                    _content = con.text.strip()
            user_prompt += f"{_content}"

        state = self.get_value_for_kwargs("state", None, **kwargs)
        summary = self.get_value_for_kwargs("summary", None, **kwargs)
        prior_info = self.get_value_for_kwargs("prior_info", None, **kwargs)
        template: str = self.get_value_for_kwargs("template", None, **kwargs)

        if not state and not summary and not prior_info and not template:
            return user_prompt

        if content:
            user_prompt += "\n\n---\n"

        if state:
            user_prompt += f"## State:\n```\n{json.dumps(state, indent=2)}\n```\n\n"

        if summary:
            user_prompt += f"## Summary:\n{summary}\n\n"

        if prior_info:
            lines = [
                f"- {key}:{chr(10).join(f'・{v}' for v in value)}"
                if isinstance(value, list)
                else f"{key}:{value}"
                for key, value in prior_info.items()
            ]
            prior = "\n".join(lines)
            user_prompt += f"## Prior Info:\n{prior}\n\n"

        if template:
            if template.startswith("file://"):
                template_file = template.replace("file://", "")
                with open(template_file, "r", encoding="utf-8") as f:
                    _template = f.read()
            else:
                _template = template

            user_prompt += f"## Template:\n```\n{_template}\n```\n\n"

        return user_prompt

    def to_dict(self) -> dict:
        """
        エージェント情報を辞書形式に変換します。
        """
        data = {
            "class": self.__class__.__name__,
            "name": self.name,
            "params": self.params,
            # "tools": self.tools,
            "call_agents": self.call_agents,
            "system_prompt": self.system_prompt,
            "llm_model_name": self.llm_client.model_name if self.llm_client else None,
            "llm_temperature": self.llm_client.temperature if self.llm_client else None,
            "llm_llm_type": self.llm_client.llm_type if self.llm_client else None,
            "llm_config": self.llm_client.config if self.llm_client else None,
        }
        return data
