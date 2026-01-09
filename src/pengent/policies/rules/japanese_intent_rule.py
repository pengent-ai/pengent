from __future__ import annotations
from typing import Any, List, Optional
import unicodedata
from .rule_base import RuleBase

DEFAULT_NEGATION_ANY = [
    "しない",
    "らない",
    "なし",
    "不要",
    "省く",
    "除外",
]

DEFAULT_MODALITY_ANY = [
    "して",
    "えて",
    "せて",
    "お願い",
    "ください",
    "たい",
    "欲しい",
    "ほしい",
    "やって",
    "でき",
    "可能",
    "でしょうか",
]

DEFAULT_SPLIT_DELIMITERS = [
    "。",
    "!",
    "！",
    "?",
    "？",
    "\n",
]


class JapaneseIntentRule(RuleBase):
    """日本語の意図を評価するルール(v1)

    判定方針:
      - 否定語が含まれる文は最優先で「意図なし」とみなす(その文は不採用)
      - 「動詞」と「モダリティ」が同一文に存在することを必須
      - 主語キーワードは同一文に無い場合、直前 context_window 文から補完する
      - 文は split_delimiters で分割(読点、は分割しない)
      - normalize=True の場合 NFKC 正規化する
    """

    def __init__(
        self,
        *,
        subject_keywords: list[str],
        verb_keywords: list[str],
        context_window: int = 1,
        proximity_chars: int = 12,
        normalize: bool = True,
        negation_any: Optional[list[str]] = None,
        modality_any: Optional[list[str]] = None,
        split_delimiters: Optional[list[str]] = None,
        score: Optional[float] = None,
    ):
        """コンストラクタ

        Args:
            subject_keywords(List[str]): 主語キーワードリスト(必須)
            verb_keywords(List[str]): 動詞キーワードリスト(必須)
            context_window(int): コンテキストウィンドウサイズ
            proximity_chars: 動詞とモダリティの近接許容文字数
            normalize(bool): 正規化(NFKC)を行うかどうか
            negation_any(List[str]): 否定分類似語リスト
            modality_any(List[str]): モダリティ分類似語リスト
              - 動詞キーワードと同時に存在する場合、肯定とみなすワード
            split_delimiters(List[str]): 文分割区切り文字リスト
            score(float): ルールのスコア
        """
        super().__init__(score=score)

        if not subject_keywords:
            raise ValueError("subject_keywords is required and must be non-empty.")
        if not verb_keywords:
            raise ValueError("verb_keywords is required and must be non-empty.")
        if context_window < 0:
            raise ValueError("context_window must be >= 0.")
        if proximity_chars < 0:
            raise ValueError("proximity_chars must be >= 0.")
        self.proximity_chars = proximity_chars

        self.subject_keywords = list(subject_keywords)
        self.verb_keywords = list(verb_keywords)
        self.context_window = context_window
        self.normalize = normalize

        # 否定分類似語リスト(デフォルト + 追加)
        self.negation_any = list(DEFAULT_NEGATION_ANY)
        if negation_any:
            self.negation_any.extend(negation_any)

        # モダリティ分類似語リスト(デフォルト + 追加)
        self.modality_any = list(DEFAULT_MODALITY_ANY)
        if modality_any:
            self.modality_any.extend(modality_any)

        # 文分割区切り文字リスト(デフォルト + 追加)
        self.split_delimiters = list(DEFAULT_SPLIT_DELIMITERS)
        if split_delimiters:
            self.split_delimiters.extend(split_delimiters)

    def set_negation_any(self, negation_any: list[str]) -> None:
        """否定分類似語リストを(完全に)置き換える"""
        self.negation_any = list(negation_any)

    def set_modality_any(self, modality_any: list[str]) -> None:
        """モダリティ分類似語リストを(完全に)置き換える"""
        self.modality_any = list(modality_any)

    def set_split_delimiters(self, split_delimiters: list[str]) -> None:
        """文分割区切り文字リストを(完全に)置き換える"""
        self.split_delimiters = list(split_delimiters)

    # ---- internal helpers ----
    def _norm(self, s: str) -> str:
        """文字列を正規化(NFKC)する"""
        if not self.normalize:
            return s
        return unicodedata.normalize("NFKC", s)

    def _contains_any(self, text: str, keywords: List[str]) -> bool:
        """text が keywords のいずれかを含むかどうか"""
        for kw in keywords:
            if self._norm(kw) in text:
                return True
        return False

    def _first_index_any(self, text: str, keywords: List[str]) -> int:
        """keywordsのどれかが最初に出現するindexを返す(なければ-1)"""
        best = -1
        for kw in keywords:
            k = self._norm(kw)
            idx = text.find(k)
            if idx != -1 and (best == -1 or idx < best):
                best = idx
        return best

    def _is_within_proximity(
        self, text: str, a_keywords: List[str], b_keywords: List[str]
    ) -> bool:
        """a_keywordsとb_keywordsがproximity_chars以内に出現するか

        Note: 片方が無ければFalseとする
        """
        a_idx = self._first_index_any(text, a_keywords)
        if a_idx == -1:
            return False
        b_idx = self._first_index_any(text, b_keywords)
        if b_idx == -1:
            return False
        return abs(a_idx - b_idx) <= self.proximity_chars

    def _split_sentences(self, text: str) -> List[str]:
        """split_delimiters により文分割(delimiter自体は捨てる)"""
        if not text:
            return []

        # 文字単位で delimiter を境界にする(regex無しで安全)
        sentences: List[str] = []
        buf: List[str] = []

        delim_set = set(self.split_delimiters)
        for ch in text:
            if ch in delim_set:
                s = "".join(buf).strip()
                if s:
                    sentences.append(s)
                buf = []
            else:
                buf.append(ch)

        tail = "".join(buf).strip()
        if tail:
            sentences.append(tail)

        return sentences

    def _has_subject_in_context(self, sentences: List[str], idx: int) -> bool:
        """idx文の主語が無い場合、直前context_window文を見て補完"""
        # まず同一文
        if self._contains_any(sentences[idx], self.subject_keywords):
            return True

        # 前文補完
        if self.context_window <= 0:
            return False

        start = max(0, idx - self.context_window)
        for j in range(idx - 1, start - 1, -1):
            # 否定文は補完元にしない
            if self._contains_any(sentences[j], self.negation_any):
                continue
            if self._contains_any(sentences[j], self.subject_keywords):
                return True

        return False

    # ---- RuleBase API ----
    def match(self, ctx: Any = None) -> bool:
        if ctx is None:
            return False

        text = self._norm(str(ctx))
        sentences = [self._norm(s) for s in self._split_sentences(text)]
        if not sentences:
            return False

        for i, sent in enumerate(sentences):
            # 否定が含まれる文は最優先で不採用(安全側)
            if self._contains_any(sent, self.negation_any):
                continue

            # 動詞とモダリティが近接していることを必須(安全側)
            if not self._is_within_proximity(
                sent, self.verb_keywords, self.modality_any
            ):
                continue

            # 主語(対象)は同一文 or 直前文から補完
            if not self._has_subject_in_context(sentences, i):
                continue

            # ここまで揃ったら intent 確定
            return True

        return False

    def describe(self) -> str:
        # デバッグ・ログ向けに「何を見るルールか」を短く出す
        return (
            "日本語意図ルール: "
            f"subject={self.subject_keywords}, "
            f"verb={self.verb_keywords}, "
            f"negation(default+extra)={self.negation_any}, "
            f"modality(default+extra)={self.modality_any}, "
            f"context_window={self.context_window}, "
            f"proximity_chars={self.proximity_chars}, "
            f"split_delimiters={self.split_delimiters}, "
            f"normalize={self.normalize}"
        )
