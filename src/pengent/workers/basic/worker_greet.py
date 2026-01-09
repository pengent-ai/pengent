from ..worker_base import WorkerBase, ExecutionContext
from ...type.llm.llm_message import LLMMessage
from ...type.llm.llm_response import LLMResponse

from ...policies import FirstMatchPolicy
from ...policies.rules import KeywordRule
from ...policies.actions import greet_action


class WorkerGreet(WorkerBase):
    """
    Worker Greet(挨拶ワーカー)クラス

        Features:
            - ユーザーに対して挨拶を行う
    """

    def __init__(self):
        policy = FirstMatchPolicy()
        policy.add_rule_and_action(
            KeywordRule("こんにちは", score=10), greet_action("ja")
        )
        policy.add_rule_and_action(KeywordRule("hello", score=5), greet_action("en"))
        super().__init__("挨拶ワーカー", policy=policy)

    def action_request(
        self, messages: list[LLMMessage], context: ExecutionContext
    ) -> LLMResponse:
        self.logger.debug("action_request start.")
        res = LLMResponse()
        message = messages[-1]  # 最新のメッセージのみを対象にする
        # Policyを実行する
        decision = self.policy.decide(message.content)
        if not decision.actions:
            res.add_content_text("[想定外の入力]:ルールポリシーにマッチしません。")
            return res
        else:
            action = decision.actions[0]
            ans = action(message.content)
            res.add_content_text(ans)
            return res
