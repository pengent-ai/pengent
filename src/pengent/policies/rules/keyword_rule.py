from .rule_base import RuleBase
from typing import Any


class KeywordRule(RuleBase):
    """特定のキーワードを含むかを評価するルール"""

    def __init__(self, keyword: str, score=None):
        super().__init__(score=score)
        self.keyword = keyword

    def match(self, ctx: Any = None) -> bool:
        if ctx is None:
            return False
        s = str(ctx)
        return self.keyword in s

    def describe(self) -> str:
        return f"'{self.keyword}' を含むかどうか"


class KeywordsAndRule(RuleBase):
    """複数のキーワードをすべて含むかを評価するルール"""

    def __init__(self, keywords: list[str], score=None):
        super().__init__(score=score)
        self.keywords = keywords

    def match(self, ctx: Any = None) -> bool:
        if ctx is None:
            return False
        s = str(ctx)
        return all(k in s for k in self.keywords)

    def describe(self) -> str:
        return f"{self.keywords} のすべてを含むかどうか"


class KeywordsOrRule(RuleBase):
    """複数のキーワードのいずれかを含むかを評価するルール"""

    def __init__(self, keywords: list[str], score=None):
        super().__init__(score=score)
        self.keywords = keywords

    def match(self, ctx: Any = None) -> bool:
        if ctx is None:
            return False
        s = str(ctx)
        return any(k in s for k in self.keywords)

    def describe(self) -> str:
        return f"{self.keywords} のいずれかを含むかどうか"
