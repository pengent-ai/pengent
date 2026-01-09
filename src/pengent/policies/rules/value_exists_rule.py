from typing import Any
from .rule_base import RuleBase


class ValueExistsRule(RuleBase):
    """値が存在しているかを評価するルール"""

    def __init__(self, key: Any, score: float | None = None):
        super().__init__(score)
        self.key = key

    def match(self, ctx: Any = None) -> bool:
        return self.key is not None

    def describe(self) -> str:
        return f"{self.key} が存在しているか評価するルール"
