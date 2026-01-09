from typing import Any, List, Optional
import unicodedata
from .rule_base import RuleBase


class KeywordAdvancedRule(RuleBase):
    """
    高機能キーワードルール

    評価順序:
      1. forbidden_any に該当したら False
      2. required_all をすべて含まなければ False
      3. any_groups を評価(AND of OR-groups)
         - min_any_groups_matched を満たさなければ False
    """

    def __init__(
        self,
        *,
        any_groups: Optional[List[List[str]]] = None,
        required_all: Optional[List[str]] = None,
        forbidden_any: Optional[List[str]] = None,
        min_any_groups_matched: Optional[int] = None,
        normalize: bool = False,
        score=None,
    ):
        """コンストラクタ

        Args:
            any_groups(List[List[str]]): 各グループ内のいずれかを含む必要がある
            required_all(List[str]): 必須キーワードリスト
            forbidden_any(List[str]): 禁止キーワードリスト
            min_any_groups_matched(Optional[int]): any_groupの達成最小値
              - 未指定なら「全グループ必須」
            normalize(bool): 正規化(NFKC)を行うかどうか
            score: ルールのスコア
        """
        super().__init__(score=score)

        self.any_groups = any_groups or []
        self.required_all = required_all or []
        self.forbidden_any = forbidden_any or []
        self.min_any_groups_matched = min_any_groups_matched
        self.normalize = normalize

        # any_groups があり、min が未指定なら「全グループ必須」
        if self.any_groups and self.min_any_groups_matched is None:
            self.min_any_groups_matched = len(self.any_groups)

    # ---------- 内部ユーティリティ ----------

    def _normalize(self, text: str) -> str:
        if not self.normalize:
            return text
        # 全角/半角・濁点などを正規化(日本語向け)
        return unicodedata.normalize("NFKC", text)

    # ---------- RuleBase API ----------

    def match(self, ctx: Any = None) -> bool:
        if ctx is None:
            return False

        text = self._normalize(str(ctx))

        # 1. forbidden_any(最優先)
        for kw in self.forbidden_any:
            if self._normalize(kw) in text:
                return False

        # 2. required_all(必須語)
        for kw in self.required_all:
            if self._normalize(kw) not in text:
                return False

        # 3. any_groups(AND of OR-groups)
        if not self.any_groups:
            return True

        matched_groups = 0
        for group in self.any_groups:
            for kw in group:
                if self._normalize(kw) in text:
                    matched_groups += 1
                    break

        return matched_groups >= (self.min_any_groups_matched or 0)

    def describe(self) -> str:
        parts = []

        if self.forbidden_any:
            parts.append(f"禁止語 {self.forbidden_any} を含まない")

        if self.required_all:
            parts.append(f"必須語 {self.required_all} をすべて含む")

        if self.any_groups:
            group_desc = []
            for g in self.any_groups:
                group_desc.append(f"({g} のいずれか)")
            parts.append(
                f"{self.min_any_groups_matched} グループ以上一致: "
                + " かつ ".join(group_desc)
            )

        if self.normalize:
            parts.append("正規化(NFKC)あり")

        return " / ".join(parts) if parts else "キーワード条件なし"
