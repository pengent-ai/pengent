from typing import Any, List
from ..actions.action_base import Action
from .policy_base import PolicyBase, Decision


class AllMatchPolicy(PolicyBase):
    """マッチしたルールのアクションをすべて実行するポリシー"""

    def decide(self, ctx: Any) -> Decision:
        actions: List[Action] = []
        total_score = 0.0
        matched_rules: List[str] = []

        for rule, action in self.rules_with_actions:
            if rule.match(ctx):
                actions.append(action)
                total_score += rule.score(ctx)
                matched_rules.append(rule.name())

        return Decision(
            matched=len(actions) > 0,
            actions=actions,
            rule_name=",".join(matched_rules) if matched_rules else None,
            score=total_score,
        )
