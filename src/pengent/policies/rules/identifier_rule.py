import re
from typing import Any, Optional
from .rule_base import RuleBase


class IdentifierRule(RuleBase):
    """
    識別子(例: コマンド名)の言及を判定する汎用ルール
    identの明示指定(名前・ラベル・ID系)

    Notes:
      - 判定方針:
        - 単語境界マッチ)(例: スペース・句読点・改行・文頭文末)を優先
        - 明示的マッチ(@ident, prefix: ident)
        - 部分マッチ(identが含まれる)
        - スコアリング(長い識別子のマッチほどスコアが高い)
      - allow_delimiters で許可された区切り文字は単語境界とみなす
      - dentが半角英数字,日本語の種類を判定(正規表現用を作成する)
    """

    def __init__(
        self,
        ident: str,
        *,
        allow_delimiters: list[str] = None,
        allow_sign: list[str] = None,
        prefix: Optional[str] = None,
        score_weights: tuple[float, float, float] = (100.0, 60.0, 10.0),
        length_bonus: float = 0.5,
    ):
        """コンストラクタ

        Args:
            ident(str): 識別子文字列(必須)
            allow_delimiters(List[str]): 単語境界として許可する区切り文字リスト
              - デフォルト: ["_", "-", ".", "/"]
            allow_sign(List[str]): 明示的マッチとして許可する接頭辞記号リスト
              - 例: ["@", "#"]
            prefix(Optional[str]): 接頭辞(例: コマンド名など)
            score_weights(tuple[float, float, float]): スコア重み
              - (明示的マッチ, 単語境界マッチ, 部分マッチ)
            length_bonus(float): 識別子長ボーナス(1文字あたり)
        """
        # スコアは可変になるためNoneに設定
        super().__init__(score=None)
        if not ident or not isinstance(ident, str):
            raise ValueError("ident は空でない文字列を指定してください。")
        self.ident = ident
        self.prefix = prefix
        self.allow_delimiters = allow_delimiters or ["_", "-", ".", "/"]
        self.allow_sign = allow_sign or ["@", "#"]
        self.w_explicit, self.w_boundary, self.w_sub = score_weights
        self.length_bonus = float(length_bonus)

        delims = re.escape("".join(self.allow_delimiters))

        # 文字種判定（正規表現用）
        if re.fullmatch(rf"[A-Za-z0-9{delims}]+", ident):
            self._char_class = r"A-Za-z0-9"
        elif re.fullmatch(rf"[一-龥々〆ぁ-んァ-ンヴー{delims}]+", ident):
            # ざっくり「和文」クラス（必要なら調整）
            self._char_class = r"一-龥々〆ぁ-んァ-ンヴー"
        else:
            raise ValueError("指定された識別子は未対応の文字種が含まれています。")
        self._setup()

    def _setup(self):
        """ルールの内部セットアップ"""
        self._len_bonus = min(len(self.ident), 30) * self.length_bonus

        ident_esc = re.escape(self.ident)
        char = self._char_class

        # 明示的マッチパターン1: 記号 + ident
        signs = self.allow_sign or []
        if signs:
            sign_class = re.escape("".join(signs))
            self._re_sign = re.compile(rf"[{sign_class}]{ident_esc}(?![{char}])")
        else:
            self._re_sign = None

        # 明示的マッチパターン2: prefix + ident
        self._re_prefix = None
        if self.prefix:
            prefix_esc = re.escape(self.prefix)
            self._re_prefix = re.compile(rf"{prefix_esc}\s*{ident_esc}(?![{char}])")

        # 単語境界マッチ
        self._re_boundary = re.compile(rf"(?<![{char}]){ident_esc}(?![{char}])")

        # 部分一致
        self._re_sub = re.compile(ident_esc)

    def evaluate(self, ctx: Any = None) -> Any:
        return self.score(ctx)

    def match(self, ctx: Any = None) -> bool:
        if ctx is None:
            return False
        return self.score(ctx) > 0.0

    def score(self, ctx: Any = None) -> float:
        if ctx is None:
            return 0.0
        text = str(ctx)

        # 明示的マッチ(記号 + ident)
        if self._re_sign is not None and self._re_sign.search(text):
            return float(self.w_explicit + self._len_bonus)

        # 明示的マッチ(prefix + ident)
        if self._re_prefix is not None and self._re_prefix.search(text):
            return float(self.w_explicit + self._len_bonus)

        # 単語境界マッチ
        if self._re_boundary.search(text):
            return float(self.w_boundary + self._len_bonus)

        # 部分マッチ
        if self._re_sub.search(text):
            return float(self.w_sub + self._len_bonus)

        return 0.0

    def describe(self) -> str:
        return (
            f"ident='{self.ident}', prefix='{self.prefix}', "
            f"allow_sign={self.allow_sign},"
            f"allow_delimiters={self.allow_delimiters}, "
            f"weights(explicit,boundary,sub)="
            f"({self.w_explicit},{self.w_boundary},{self.w_sub}), "
            f"length_bonus={self.length_bonus}"
        )
