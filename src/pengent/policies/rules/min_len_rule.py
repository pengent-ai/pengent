from .rule_base import RuleBase
from typing import Any


class MinLenRule(RuleBase):
    """長さが指定の最小値以上かを評価するルール"""

    def __init__(self, min_len: int, score: float | None = None):
        super().__init__(score=score)
        self.min_len = min_len

    def match(self, ctx: Any = None) -> bool:
        if ctx is None:
            return False
        try:
            return len(ctx) >= self.min_len
        except TypeError:
            return False

    def describe(self) -> str:
        return f"長さが {self.min_len} 以上かどうか"
