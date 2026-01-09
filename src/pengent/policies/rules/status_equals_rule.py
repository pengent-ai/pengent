from ..rules.rule_base import RuleBase
from typing import Any


class StatusEqualsRule(RuleBase):
    """値が特定の値と等しいかを評価するルール"""

    def __init__(self, key, expected_value, score=None):
        super().__init__(score)
        self.key = key
        self.expected_value = expected_value

    def match(self, ctx: Any = None) -> bool:
        return self.key == self.expected_value

    def describe(self) -> str:
        return f"{self.key} が {self.expected_value} かどうか"
