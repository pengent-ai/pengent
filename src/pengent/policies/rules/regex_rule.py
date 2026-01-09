from .rule_base import RuleBase
import re
from typing import Any


class RegexRule(RuleBase):
    """正規表現にマッチするかを評価するルール"""

    def __init__(self, pattern: str, flags: int = 0, score=None):
        """
        :param pattern: 正規表現パターン文字列
        :param flags: re.IGNORECASE などのフラグ(省略可)
        """
        super().__init__(score=score)
        self.pattern = pattern
        self.flags = flags
        self._compiled = re.compile(pattern, flags)

    def match(self, ctx: Any = None) -> bool:
        # ctx を文字列として扱う(NoneはFalse)
        if ctx is None:
            return False
        s = str(ctx)
        return bool(self._compiled.search(s))

    def describe(self) -> str:
        return f"正規表現 '{self.pattern}' にマッチするかどうか"
