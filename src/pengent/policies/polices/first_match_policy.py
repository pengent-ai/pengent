from typing import Any
from .policy_base import PolicyBase, Decision


class FirstMatchPolicy(PolicyBase):
    """最初にマッチしたルールのアクションを実行するポリシー"""

    def decide(self, ctx: Any) -> Decision:
        for rule, action in self.rules_with_actions:
            if rule.match(ctx):
                return Decision(
                    matched=True,
                    actions=[action],
                    rule_name=rule.name(),
                    score=rule.score(ctx),
                )
        return Decision(matched=False)
