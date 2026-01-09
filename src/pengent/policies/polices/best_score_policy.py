from typing import Any, Optional
from ..actions.action_base import Action
from .policy_base import PolicyBase, Decision


class BestScorePolicy(PolicyBase):
    """最もスコアが高いルールのアクションを採用するポリシー(同点は先勝ち)"""

    def decide(self, ctx: Any) -> Decision:
        best_action: Optional[Action] = None
        best_rule_name: Optional[str] = None
        best_score = 0.0
        found = False

        for rule, action in self.rules_with_actions:
            if rule.match(ctx):
                s = rule.score(ctx)
                found = True
                if (best_action is None) or (s > best_score):
                    best_action = action
                    best_rule_name = rule.name()
                    best_score = s

        if found and best_action is not None:
            return Decision(
                matched=True,
                actions=[best_action],
                rule_name=best_rule_name,
                score=best_score,
            )

        return Decision(matched=False, actions=[], score=0.0)
