from abc import ABC, abstractmethod
from typing import Any, List, Tuple, Optional
from dataclasses import dataclass, field
from ..rules.rule_base import RuleBase
from ..actions.action_base import Action


@dataclass
class Decision:
    """ポリシーの判断結果"""

    matched: bool
    actions: List[Action] = field(default_factory=list)
    rule_name: Optional[str] = None
    score: float = 0.0


class PolicyBase(ABC):
    """ポリシーの基底クラス"""

    def __init__(self):
        self.rules_with_actions: List[Tuple[RuleBase, Action]] = []

    def add_rule_and_action(self, rule: RuleBase, action: Action) -> None:
        self.rules_with_actions.append((rule, action))

    @abstractmethod
    def decide(self, ctx: Any) -> Decision:
        """アクションを判断する"""
        raise NotImplementedError

    def run(self, ctx: Any) -> Any:
        """アクションを判断して実行"""
        decision = self.decide(ctx)
        results = []
        for action in decision.actions:
            results.append(action(ctx, decision))
        return results
