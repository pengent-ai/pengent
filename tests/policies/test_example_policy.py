from unittest.mock import patch

from pengent.policies import (
    FirstMatchPolicy,
    AllMatchPolicy,
    ThresholdPolicy,
    ThresholdFilterPolicy,
    ThresholdTriggerPolicy,
    ThresholdBestPolicy,
    BestScorePolicy,
)
from pengent.policies.rules.keyword_rule import KeywordRule
from pengent.policies.actions import greet_action


GREETING = "GREETING"


@patch(
    "pengent.policies.actions.action_base.random.choice",
    return_value=GREETING,
)
def test_first_match_policy_decide_and_run(mock_choice):
    policy = FirstMatchPolicy()
    policy.add_rule_and_action(KeywordRule("こんにちは", score=10), greet_action("ja"))
    policy.add_rule_and_action(KeywordRule("hello", score=5), greet_action("en"))

    decision = policy.decide("こんにちは！")
    results = policy.run("こんにちは！")

    assert decision.matched is True
    assert decision.rule_name == "KeywordRule"
    # 最初にマッチしたルールのみを採用
    assert decision.score == 10
    assert len(decision.actions) == 1
    assert results == [GREETING]
    mock_choice.assert_called()


@patch(
    "pengent.policies.actions.action_base.random.choice",
    return_value=GREETING,
)
def test_all_match_policy_matches_all(mock_choice):
    policy = AllMatchPolicy()
    policy.add_rule_and_action(KeywordRule("hello", score=5), greet_action("en"))
    policy.add_rule_and_action(KeywordRule("こんにちは", score=10), greet_action("ja"))
    policy.add_rule_and_action(KeywordRule("!", score=1), greet_action("ja"))

    decision = policy.decide("こんにちは!")
    results = policy.run("こんにちは!")

    assert decision.matched is True
    assert decision.score == 11
    assert decision.rule_name == "KeywordRule,KeywordRule"
    assert len(decision.actions) == 2
    assert results == [GREETING, GREETING]
    assert mock_choice.call_count == 2


@patch(
    "pengent.policies.actions.action_base.random.choice",
    return_value=GREETING,
)
def test_threshold_policy_hits_threshold(mock_choice):
    policy = ThresholdPolicy(threshold=10)
    policy.add_rule_and_action(KeywordRule("hello", score=5), greet_action("en"))
    policy.add_rule_and_action(KeywordRule("こんにちは", score=9), greet_action("ja"))
    policy.add_rule_and_action(KeywordRule("!", score=1), greet_action("ja"))

    decision = policy.decide("こんにちは!")
    results = policy.run("こんにちは!")

    assert decision.matched is True
    # 合計スコアはマッチした全ルールの合算(9+1)
    assert decision.score == 10
    assert len(decision.actions) == 2
    assert results == [GREETING, GREETING]
    assert mock_choice.call_count == 2


def test_threshold_policy_below_threshold():
    policy = ThresholdPolicy(threshold=10)
    policy.add_rule_and_action(KeywordRule("hello", score=5), greet_action("en"))
    policy.add_rule_and_action(KeywordRule("こんにちは", score=9), greet_action("ja"))

    decision = policy.decide("hello")
    results = policy.run("hello")

    assert decision.matched is False
    assert decision.score == 5
    assert decision.actions == []
    assert results == []


@patch(
    "pengent.policies.actions.action_base.random.choice",
    return_value=GREETING,
)
def test_threshold_filter_policy_filters_by_score(mock_choice):
    policy = ThresholdFilterPolicy(threshold=10)
    policy.add_rule_and_action(KeywordRule("hello", score=5), greet_action("en"))
    policy.add_rule_and_action(KeywordRule("こんにちは", score=10), greet_action("ja"))
    policy.add_rule_and_action(KeywordRule("!", score=1), greet_action("ja"))

    decision = policy.decide("こんにちは!")
    results = policy.run("こんにちは!")

    assert decision.matched is True
    assert len(decision.actions) == 1
    assert results == [GREETING]
    assert decision.score == 11  # 合計スコアを返す実装
    mock_choice.assert_called_once()


def test_threshold_filter_policy_no_match():
    policy = ThresholdFilterPolicy(threshold=10)
    policy.add_rule_and_action(KeywordRule("hello", score=5), greet_action("en"))

    decision = policy.decide("no hit")

    assert decision.matched is False
    assert decision.actions == []
    assert decision.score == 0


@patch(
    "pengent.policies.actions.action_base.random.choice",
    return_value=GREETING,
)
def test_threshold_trigger_policy_triggers_once(mock_choice):
    trigger = greet_action("en")
    policy = ThresholdTriggerPolicy(threshold=10, trigger_action=trigger)
    policy.add_rule_and_action(KeywordRule("hello", score=5), None)
    policy.add_rule_and_action(KeywordRule("こんにちは", score=9), None)
    policy.add_rule_and_action(KeywordRule("!", score=1), None)

    decision = policy.decide("こんにちは!")
    results = policy.run("こんにちは!")

    assert decision.matched is True
    assert decision.score == 10
    assert decision.actions == [trigger]
    assert results == [GREETING]
    mock_choice.assert_called_once()


def test_threshold_trigger_policy_below_threshold():
    trigger = greet_action("en")
    policy = ThresholdTriggerPolicy(threshold=10, trigger_action=trigger)
    policy.add_rule_and_action(KeywordRule("hello", score=5), None)
    policy.add_rule_and_action(KeywordRule("こんにちは", score=9), None)

    decision = policy.decide("hello")
    results = policy.run("hello")

    assert decision.matched is False
    assert decision.actions == []
    assert decision.score == 5
    assert results == []


@patch(
    "pengent.policies.actions.action_base.random.choice",
    return_value=GREETING,
)
def test_threshold_best_policy_best_action(mock_choice):
    policy = ThresholdBestPolicy(threshold=10)
    policy.add_rule_and_action(KeywordRule("hello", score=5), greet_action("en"))
    policy.add_rule_and_action(KeywordRule("こんにちは", score=10), greet_action("ja"))
    policy.add_rule_and_action(KeywordRule("!", score=1), greet_action("ja"))

    decision = policy.decide("こんにちは!")
    results = policy.run("こんにちは!")

    assert decision.matched is True
    assert decision.rule_name == "KeywordRule"
    assert decision.score == 11
    assert decision.actions[0].description.startswith("Greeting action")
    assert results == [GREETING]
    mock_choice.assert_called_once()


def test_threshold_best_policy_under_threshold():
    policy = ThresholdBestPolicy(threshold=10)
    policy.add_rule_and_action(KeywordRule("hello", score=5), greet_action("en"))
    policy.add_rule_and_action(KeywordRule("こんにちは", score=9), greet_action("ja"))

    decision = policy.decide("hello")
    results = policy.run("hello")

    assert decision.matched is False
    assert decision.actions == []
    assert decision.score == 5
    assert results == []


@patch(
    "pengent.policies.actions.action_base.random.choice",
    return_value=GREETING,
)
def test_best_score_policy_selects_highest(mock_choice):
    policy = BestScorePolicy()
    policy.add_rule_and_action(KeywordRule("hello", score=11), greet_action("en"))
    policy.add_rule_and_action(KeywordRule("こんにちは", score=10), greet_action("ja"))
    policy.add_rule_and_action(KeywordRule("!", score=1), greet_action("ja"))

    decision = policy.decide("こんにちは!")
    results = policy.run("こんにちは!")

    assert decision.matched is True
    assert decision.rule_name == "KeywordRule"
    assert decision.score == 10
    assert results == [GREETING]
    mock_choice.assert_called_once()
