from abc import ABC, abstractmethod
from typing import Any


class RuleBase(ABC):
    """ルールの基底クラス(条件判定 + スコア/返却値マッピング)"""

    def __init__(self, score: float | None = None):
        if score is None:
            self._true_value: Any = True
            self._false_value: Any = False
        else:
            self._true_value: Any = score
            self._false_value: Any = 0

    def set_return_value(self, true_value: Any, false_value: Any = None) -> None:
        """ルールの評価結果の返却値を設定する"""
        self._true_value = true_value
        self._false_value = false_value

    def set_score_value(self, score: float) -> None:
        """ルールの評価結果のスコア値を設定する"""
        self._true_value = score
        self._false_value = 0

    @abstractmethod
    def match(self, ctx: Any = None) -> bool:
        """条件判定(True/False)"""
        raise NotImplementedError

    def evaluate(self, ctx: Any = None) -> Any:
        """条件判定に応じた返却値(score/True/False/任意)を返す"""
        return self._true_value if self.match(ctx) else self._false_value

    def score(self, ctx: Any = None) -> float:
        """評価結果が数値なら返す。数値でなければ0。"""
        v = self.evaluate(ctx)
        return float(v) if isinstance(v, (int, float)) else 0.0

    @abstractmethod
    def describe(self) -> str:
        raise NotImplementedError

    def name(self) -> str:
        return self.__class__.__name__

    def __repr__(self):
        return f"{self.__class__.__name__}({self.describe()})"

    def dump(self, ctx: Any = None) -> str:
        """ルールの詳細情報を文字列で返す"""
        match_result = self.match(ctx)
        score_value = self.score(ctx)
        return (
            f"--- Rule Dump ---\n"
            f"Rule: {self.name()}\n"
            f" Description: {self.describe()}\n"
            f" Match: {match_result}\n"
            f" Score: {score_value}\n"
            f"-----------------"
        )
