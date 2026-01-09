from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Union, Any
import re

from .rule_base import RuleBase


CheckType = Literal["contains", "contains_any", "equals", "regex", "empty", "not_empty"]


@dataclass(frozen=True)
class LineCondition:
    """1行に対する条件"""

    line_number: int  # 0-indexed
    check_type: CheckType
    value: Union[str, List[str]] = ""

    def check(self, lines: List[str]) -> bool:
        if self.line_number < 0 or self.line_number >= len(lines):
            return False

        target_line = lines[self.line_number].strip()

        if self.check_type == "contains":
            return isinstance(self.value, str) and (self.value in target_line)

        if self.check_type == "contains_any":
            return isinstance(self.value, list) and any(
                v in target_line for v in self.value
            )

        if self.check_type == "equals":
            return isinstance(self.value, str) and (self.value == target_line)

        if self.check_type == "regex":
            return isinstance(self.value, str) and bool(
                re.search(self.value, target_line)
            )

        if self.check_type == "empty":
            return target_line == ""

        if self.check_type == "not_empty":
            return target_line != ""

        return False


class GenericLineRule(RuleBase):
    """各行毎に条件を評価するルール"""

    def __init__(self, conditions: List[LineCondition], score=None):
        super().__init__(score=score)
        self.conditions = conditions

    def match(self, ctx: Any = None) -> bool:
        if ctx is None:
            return False
        text = str(ctx)
        lines = text.splitlines()
        return all(cond.check(lines) for cond in self.conditions)

    def describe(self) -> str:
        tmp = ["各行毎に評価を行う"]
        for cond in self.conditions:
            ln = cond.line_number + 1
            if cond.check_type == "contains":
                tmp.append(f"{ln}行目に'{cond.value}'が含まれるか")
            elif cond.check_type == "contains_any":
                tmp.append(f"{ln}行目に{cond.value}のいずれかが含まれるか")
            elif cond.check_type == "equals":
                tmp.append(f"{ln}行目が'{cond.value}'と等しいか")
            elif cond.check_type == "regex":
                tmp.append(f"{ln}行目が正規表現'{cond.value}'に一致するか")
            elif cond.check_type == "empty":
                tmp.append(f"{ln}行目が空か")
            elif cond.check_type == "not_empty":
                tmp.append(f"{ln}行目が空でないか")
        return ",".join(tmp)
