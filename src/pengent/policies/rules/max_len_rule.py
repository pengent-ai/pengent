from .rule_base import RuleBase
from typing import Any


class MaxLenRule(RuleBase):
    """長さが指定の最大値以下かを評価するルール"""

    def __init__(self, max_len: int, score=None):
        super().__init__(score=score)
        self.max_len = max_len

    def match(self, ctx: Any = None) -> bool:
        if ctx is None:
            return False
        try:
            return len(ctx) <= self.max_len
        except TypeError:
            return False

    def describe(self) -> str:
        return f"長さが {self.max_len} 以下かどうか"
