from typing import Any, List, Optional, Tuple
from ..actions.action_base import Action
from .policy_base import PolicyBase, Decision


class ThresholdPolicy(PolicyBase):
    """合計スコアが閾値以上なら、マッチしたアクションを実行するポリシー"""

    def __init__(self, threshold: float):
        super().__init__()
        self.threshold = threshold

    def decide(self, ctx: Any) -> Decision:
        matched_actions: List[Action] = []
        total_score = 0.0
        matched_rules: List[str] = []

        for rule, action in self.rules_with_actions:
            if rule.match(ctx):
                matched_actions.append(action)
                total_score += rule.score(ctx)
                matched_rules.append(rule.name())

        if total_score >= self.threshold and matched_actions:
            return Decision(
                matched=True,
                actions=matched_actions,
                rule_name=",".join(matched_rules),
                score=total_score,
            )

        # 閾値未達なら実行しない
        return Decision(
            matched=False,
            actions=[],
            rule_name=",".join(matched_rules) if matched_rules else None,
            score=total_score,
        )


class ThresholdFilterPolicy(PolicyBase):
    """スコアが閾値以上のルールだけ実行"""

    def __init__(self, threshold: float):
        super().__init__()
        self.threshold = threshold

    def decide(self, ctx: Any) -> Decision:
        actions = []
        for rule, action in self.rules_with_actions:
            if rule.match(ctx) and rule.score(ctx) >= self.threshold:
                actions.append(action)

        return Decision(
            matched=len(actions) > 0,
            actions=actions,
            score=sum(rule.score(ctx) for rule, _ in self.rules_with_actions),
        )


class ThresholdTriggerPolicy(PolicyBase):
    """合計スコアが閾値以上なら、固定のアクションを1回だけ実行する"""

    def __init__(self, threshold: float, trigger_action: Action):
        super().__init__()
        self.threshold = threshold
        self.trigger_action = trigger_action

    def decide(self, ctx: Any) -> Decision:
        total_score = 0.0
        matched_rules: List[str] = []

        for rule, _action in self.rules_with_actions:
            if rule.match(ctx):
                total_score += rule.score(ctx)
                matched_rules.append(rule.name())

        if total_score >= self.threshold:
            return Decision(
                matched=True,
                actions=[self.trigger_action],
                rule_name=",".join(matched_rules) if matched_rules else None,
                score=total_score,
            )

        return Decision(
            matched=False,
            actions=[],
            rule_name=",".join(matched_rules) if matched_rules else None,
            score=total_score,
        )


class ThresholdBestPolicy(PolicyBase):
    """合計スコアが閾値以上なら、
    最もスコアが高い1件だけ実行する(同点は先勝ち)
    """

    def __init__(self, threshold: float):
        super().__init__()
        self.threshold = threshold

    def decide(self, ctx: Any) -> Decision:
        total_score = 0.0
        matched_rules: List[str] = []

        # (score, rule_name, action)
        best: Optional[Tuple[float, str, Action]] = None

        for rule, action in self.rules_with_actions:
            if rule.match(ctx):
                s = rule.score(ctx)
                total_score += s
                rn = rule.name()
                matched_rules.append(rn)

                if best is None or s > best[0]:
                    best = (s, rn, action)

        if best is not None and total_score >= self.threshold:
            best_score, best_rule_name, best_action = best
            return Decision(
                matched=True,
                actions=[best_action],
                rule_name=best_rule_name,  # 採用ルール名
                score=total_score,  # 合計スコア
            )

        return Decision(
            matched=False,
            actions=[],
            rule_name=",".join(matched_rules) if matched_rules else None,
            score=total_score,
        )
