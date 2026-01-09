import re
from typing import Any
from ..worker_base import WorkerBase, ExecutionContext
from ...type.llm.llm_message import LLMMessage
from ...type.llm.llm_response import LLMResponse

from ...tools import ToolUnion, ToolBase

from ...policies.rules import JapaneseIntentRule, IdentifierRule
from ...policies.actions import Action, choice_action
from ...policies import ThresholdBestPolicy


class ToolParameterCollector:
    """ツールのパラメータを収集するクラス"""

    def __init__(self, tool_base: ToolBase, collected_params: dict = None):
        self.tool_base = tool_base

        parameters = self.tool_base.parameters_schema()
        self.required_keys: list = parameters.get("required", [])
        self.param_defs: dict = parameters.get("properties", {})

    def is_ready(self, collected_params) -> bool:
        """必須パラメータがすべて収集されているか確認"""
        if not self.required_keys or all(
            key in (collected_params or {}) for key in self.required_keys
        ):
            return True
        else:
            return False

    def set_parameters(self, content: str, collected_params: dict):
        lines = content.strip().splitlines()

        current_key: str = None
        current_value_lines = []

        def store_current():
            nonlocal current_key, current_value_lines
            if not current_key:
                return

            key = current_key.strip()
            if key not in self.param_defs:
                current_key = None
                current_value_lines = []
                return

            value = "\n".join(current_value_lines).strip()
            collected_params[current_key.strip()] = value
            current_key = None
            current_value_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 複数行開始形式: key: や key;
            multi_match = re.match(r"^(\w+)\s*[:;]\s*$", line)
            if multi_match:
                store_current()
                k = multi_match.group(1)
                if k not in self.param_defs:
                    current_key = None
                    current_value_lines = []
                    continue

                current_key = multi_match.group(1)
                current_value_lines = []
                continue

            # 単一行形式: key=value や key: value や keyはvalueです
            # single_match = re.match(r"^(\w+)\s*(=|:|は)\s*(.+)$", line)
            single_match = re.search(
                r"([a-zA-Z_][a-zA-Z0-9_]*)\s*(=|:|は)\s*(.+)", line
            )
            if single_match:
                store_current()
                key = single_match.group(1)
                value = single_match.group(3).strip()

                if key not in self.param_defs:
                    continue

                value = normalize_query(value)
                if value == "" or value.lower() in ["none", "null", "nil"]:
                    collected_params.pop(key, None)
                else:
                    collected_params[key.strip()] = value

                current_key = None
                current_value_lines = []
                continue

            # 複数行中の行
            if current_key:
                current_value_lines.append(line)

        store_current()  # 最後に残ったものを保存
        return

    def make_message(self, collected_params: dict = None) -> str:
        lines = []
        lines.append(
            "【選択中のツール】:\n- ツール名: {self.tool_base.name}\n"
            "- 説明:{self.tool_base.description}\n"
            "\n"
        )

        # 現在設定されているパラメータ
        if collected_params:
            lines.append("【設定中のパラメータ】")
            for key, val in collected_params.items():
                val_str = str(val)
                val_summary = val_str if len(val_str) <= 50 else val_str[:47] + "..."
                lines.append(f"- `{key}`: {val_summary}")
            lines.append("\n")

        if self.is_ready(collected_params):
            lines.extend(
                [
                    "必須パラメータはすべて設定されています。",
                    "このツールを実行できます。よろしいですか? (はい /実行 など)",
                ]
            )
            lines.append("\n")
        else:
            lines.append("【不足の必須パラメータ】")
            for key in self.required_keys:
                if collected_params and key in collected_params:
                    continue
                param_def = self.param_defs.get(key, {})
                param_type = param_def.get("type", "string")
                description = param_def.get("description", "")
                lines.append(f"- `{key}`: [型: {param_type}] {description}")
            lines.append("\n")
            lines.extend(
                [
                    "必須パラメータが未入力の場合は、ツールを実行できません。",
                    "パラメータを設定してください。",
                ]
            )
            lines.append("\n")

        # 未設定の任意パラメータ
        cp = collected_params or {}
        optional_keys = [
            k for k in self.param_defs if k not in self.required_keys and k not in cp
        ]

        if optional_keys:
            lines.append("\n### 任意で設定できるパラメータ")
            for key in optional_keys:
                param_def = self.param_defs.get(key, {})
                param_type = param_def.get("type", "string")
                description = param_def.get("description", "")
                lines.append(f"- `{key}`: {description} [型: {param_type}]")

        lines.append("---\n")
        return "\n".join(lines)

    def get_tool_help(self) -> str:
        lines = []
        lines.append(
            f"【選択中のツール】:\n- ツール名: {self.tool_base.name}\n"
            f"- 説明:{self.tool_base.description}\n"
            "\n"
        )
        lines.append("【ツールのパラメータ】")
        for key, param_def in self.param_defs.items():
            param_type = param_def.get("type", "string")
            description = param_def.get("description", "")
            required_str = "必須" if key in self.required_keys else "任意"
            lines.append(f"- `{key}`: [型: {param_type}, {required_str}]{description}")

        lines.append("\n")
        return "\n".join(lines)

    def get_help(self) -> str:
        return (
            "【引数の設定方法\n\n】"
            "**設定方法1(1行ずつ入力)**\n"
            "- `key=value`\n"
            "- `key: value`\n"
            "- `keyはvalueです`\n\n"
            "#### 設定方法2(複数行入力)\n"
            "- `key:` または `key;` のあとに改行して値を入力\n"
            "- 例：\n"
            "  ```\n"
            "  <KEY>:\n"
            "  <pengent-dev>\n"
            "  ```\n"
            "- JSONやリストなど複雑な型はコードブロック(```)で囲ってください\n"
            "\n"
        )


def normalize_query(value: str) -> str:
    v = value.strip()

    # 末尾の丁寧語・依頼表現を削る（必要に応じて追加）
    v = re.sub(
        r"(で)?(お願い(します)?|ください|です|だよ|だ|にして|にしてね|にして下さい)\s*$",
        "",
        v,
    ).strip()
    return v


class WorkerCallTool(WorkerBase):
    """
    ツール呼び出しワーカークラス
    """

    def __init__(
        self,
        name: str = "ツール呼び出しワーカー",
        params: dict = None,
        tools: list[ToolUnion] = None,
        logger=None,
    ):
        """
        コンストラクタ
        """
        super().__init__(name, params=params, tools=tools, logger=logger)

    def action_request(
        self, messages: list[LLMMessage], context: ExecutionContext
    ) -> LLMResponse:
        self.logger.debug("action_request start.")
        # ツール呼び出し結果の処理
        # if (messages[-1].create_tools_result)
        state: dict = context.state
        res = LLMResponse()
        content: str = messages[-1].content
        res_msg = []
        if messages[-1].tool_call_id:
            # ツール呼び出し結果の処理
            res.add_content_text(
                (
                    "ツールの実行が完了しました。結果を確認してください。\n\n"
                    f"ツール結果:\n{messages[-1].content}"
                )
            )
            return res

        if self.tools is None or len(self.tools) == 0:
            res.add_content_text(
                "ワーカーにツールが設定されていません。\n管理者に問い合わせてください。"
            )
            return res

        # ツール一覧の表示要求
        if JapaneseIntentRule(
            subject_keywords=[
                "ツール",
                "一覧",
            ],
            verb_keywords=[
                "教",
                "知り",
                "見",
            ],
            negation_any=["パラメータ", "引数"],
        ).match(content):
            _action = self._get_tool_list_action(self._tool_map)
            res.add_content_text(_action())
            return res

        # ツール名の選択
        tool_name = state.get("tool_name")
        if not tool_name:
            if len(self.tools) > 1:
                # ツール呼び出し結果の処理(使いたいツールが存在する場合)
                policy = ThresholdBestPolicy(threshold=0.5)
                for key in self._tool_map.keys():
                    policy.add_rule_and_action(
                        rule=IdentifierRule(ident=key),
                        action=choice_action(key, f"choice_{key}"),
                    )
                _rets = policy.run(ctx=content)
                if _rets:
                    tool_name = _rets[0]
                    tool_base = self._tool_map.get(tool_name)
                    context.set_state_delta("tool_name", tool_name)
                else:
                    # 選択するツールが存在しない場合
                    res_msg.append("続けるにはツールの選択が必要です。")
                    res_msg.append("以下のツール一覧から選択してください。\n")
                    res_msg.append(self._get_tool_list_action(self._tool_map)())
                    res.add_content_text("\n".join(res_msg))
                    return res
            else:
                tool_name = self.tools[0].name
                context.set_state_delta("tool_name", self.tools[0].name)

        tool_base = self._tool_map.get(tool_name)
        collected_params = dict(state.get("collected_params") or {})
        is_confirming = state.get("is_confirming", False)

        # ツールを選びなおす(リセット)
        if JapaneseIntentRule(
            subject_keywords=[
                "ツール",
                "関数",
            ],
            verb_keywords=[
                "選び",
                "リセット",
                "選択",
                "変え",
                "やり直し",
            ],
            negation_any=["パラメータ", "引数"],
        ).match(content):
            if len(self.tools) > 1:
                # ツール名が選択されているのか確認する必要がある
                context.set_state_delta("is_confirming", None)
                context.set_state_delta("collected_params", None)
                context.set_state_delta("tool_name", None)
                res.add_content_text("ツールの選択をリセットしました。")
            else:
                res.add_content_text(
                    "利用可能なツールは1つだけです。"
                    "ご希望のツールが存在しない場合は、管理者に問い合わせてください。"
                )
            return res

        # ツールパラメータのヘルプ要求
        if JapaneseIntentRule(
            subject_keywords=["パラメータ", "引数"],
            verb_keywords=["設定し", "方法", "やり方", "教え", "知りたい"],
            modality_any=["は"],
        ).match(content):
            tool_param_collector = ToolParameterCollector(tool_base, collected_params)
            res_msg.append(tool_param_collector.get_tool_help())
            res_msg.append(tool_param_collector.get_help())
            res.add_content_text("\n".join(res_msg))
            return res

        if is_confirming and content.strip().lower() in (
            "はい",
            "実行",
            "ok",
            "yes",
            "承認",
            "お願いします",
        ):
            # 確認中でOKならツール実行
            context.set_state_delta("is_confirming", None)
            context.set_state_delta("collected_params", None)
            context.set_state_delta("tool_name", None)
            res.add_content_tools(
                tools=[
                    {
                        "id": "worker_call_tool_1",
                        "type": "function",
                        "function": {
                            "name": tool_base.name,
                            "arguments": collected_params,
                        },
                    }
                ]
            )
            return res
        else:
            # ツール実行が未確認の場合
            tool_param_collector = ToolParameterCollector(tool_base, collected_params)

            tool_param_collector.set_parameters(content, collected_params)
            context.set_state_delta("collected_params", collected_params)

            if tool_param_collector.is_ready(collected_params):
                context.set_state_delta("is_confirming", True)
            else:
                context.set_state_delta("is_confirming", False)

            # パラメータ収集中メッセージを返す
            res_msg.append(tool_param_collector.make_message(collected_params))
            res.add_content_text("\n".join(res_msg))
            return res

    @staticmethod
    def _get_tool_list_action(tool_map: dict[str, ToolBase]) -> Action:
        def get_tool_list(ctx: Any = None, decision: Any = None) -> str:
            # ツール一覧の表示要求
            help_lines = [
                "【利用可能なツール一覧】",
                "",
                "**ツール名**:",
            ]
            for tool in tool_map.values():
                help_lines.append(f"- {tool.name} - {tool.description}\n")
                help_lines.append("")
            return "\n".join(help_lines)

        return Action(
            name="get_tool_list",
            fn=get_tool_list,
            description="利用可能なツールの一覧を取得するアクション",
        )
