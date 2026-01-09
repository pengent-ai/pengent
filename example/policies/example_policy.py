import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
)
from pengent.policies import (
    FirstMatchPolicy,
    AllMatchPolicy,
    ThresholdPolicy,
    ThresholdFilterPolicy,
    ThresholdTriggerPolicy,
    ThresholdBestPolicy,
    BestScorePolicy,
)
from pengent.policies.rules import KeywordRule,IdentifierRule
from pengent.policies.actions import greet_action, choice_action
from pengent.lib import get_logger
logger = get_logger(level=10)

def example_policy_first_match():
    logger.info("start example_policy_first_match")
    # 最初にマッチしたルールを適用するポリシーの作成
    policy = FirstMatchPolicy()
    # ルールとアクションの紐付け(順序が優先順位)
    policy.add_rule_and_action(
        KeywordRule("こんにちは", score=10),
        greet_action("ja")
    )
    policy.add_rule_and_action(
        KeywordRule("hello", score=5),
        greet_action("en")
    )

    for text in ["こんにちは！", "hello there", "no match..."]:
        results = policy.run(text)
        decision = policy.decide(text)
        print("----")
        print(f"input text: {text}")
        print("decision:", decision)
        print("results:", results)


def example_policy_all_match():
    logger.info("start example_policy_all_match")
    # 最初にマッチしたルールを適用するポリシーの作成
    policy = AllMatchPolicy()
    # ルールとアクションの紐付け(順序が優先順位)
    policy.add_rule_and_action(
        KeywordRule("hello", score=5),
        greet_action("en")
    )
    policy.add_rule_and_action(
        KeywordRule("こんにちは", score=10),
        greet_action("ja")
    )
    policy.add_rule_and_action(
        KeywordRule("!", score=1),
        greet_action("ja")
    )

    print(policy.run("こんにちは!"))
    # ２つ目と３つ目のルールがマッチするはず(2回出力)

def example_policy_threshold():
    # 「各ルールのスコアを合算して、
    # 合計(トータルスコア)が閾値以上なら実行する」
    logger.info("start example_policy_threshold")
    # 最初にマッチしたルールを適用するポリシーの作成
    policy = ThresholdPolicy(threshold=10)
    # ルールとアクションの紐付け(順序が優先順位)
    policy.add_rule_and_action(
        KeywordRule("hello", score=5),
        greet_action("en")
    )
    policy.add_rule_and_action(
        KeywordRule("こんにちは", score=9),
        greet_action("ja")
    )
    policy.add_rule_and_action(
        KeywordRule("!", score=1),
        greet_action("ja")
    )

    print(policy.run("こんにちは!"))
    # トータルで閾値10を超えた時に当てはまったルールの全てが実行される

def example_policy_threshold_filter():
    logger.info("start example_policy_threshold_filter")
    # スコアが閾値以上のルールだけ実行するポリシーの作成
    policy = ThresholdFilterPolicy(threshold=10)
    # ルールとアクションの紐付け(順序が優先順位)
    policy.add_rule_and_action(
        KeywordRule("hello", score=5),
        greet_action("en")
    )
    policy.add_rule_and_action(
        KeywordRule("こんにちは", score=10),
        greet_action("ja")
    )
    policy.add_rule_and_action(
        KeywordRule("!", score=1),
        greet_action("ja")
    )

    print(policy.run("こんにちは!"))
    # ２つ目のルールのみが実行される

def example_policy_threshold_trigger():
    logger.info("start example_policy_threshold_trigger")
    # 合計スコアが閾値以上なら、固定のアクションを1回だけ実行するポリシーの作成
    policy = ThresholdTriggerPolicy(
        threshold=10,
        trigger_action=greet_action("en"),
    )
    # ルールとアクションの紐付け(順序が優先順位)
    policy.add_rule_and_action(KeywordRule("hello", score=5),None)
    policy.add_rule_and_action(KeywordRule("こんにちは", score=9),None)
    policy.add_rule_and_action(KeywordRule("!", score=1),None)

    print(policy.run("こんにちは!"))
    # 閾値を超えた場合にのみ、固定のアクションが1回実行される

def example_policy_threshold_best():
    logger.info("start example_policy_threshold_best")
    # 合計スコアが閾値以上なら、
    # 最もスコアの高いルールのアクションを実行するポリシーの作成
    policy = ThresholdBestPolicy(threshold=10)
    # ルールとアクションの紐付け(順序が優先順位)
    policy.add_rule_and_action(
        KeywordRule("hello", score=5),
        greet_action("en")
    )
    policy.add_rule_and_action(
        KeywordRule("こんにちは", score=10),
        greet_action("ja")
    )
    policy.add_rule_and_action(
        KeywordRule("!", score=1),
        greet_action("ja")
    )

    print(policy.run("こんにちは!"))
    # ２つ目のルールのみが実行される


def example_policy_best_score():
    logger.info("start example_policy_best_score")
    # 最初にマッチしたルールを適用するポリシーの作成
    policy = BestScorePolicy()
    # ルールとアクションの紐付け(順序が優先順位)
    policy.add_rule_and_action(
        KeywordRule("hello", score=11),
        greet_action("en")
    )
    policy.add_rule_and_action(
        KeywordRule("こんにちは", score=10),
        greet_action("ja")
    )
    policy.add_rule_and_action(
        KeywordRule("!", score=1),
        greet_action("ja")
    )

    print(policy.run("こんにちわ!"))
    # 最もスコアの高いルールのみが実行される
    # ２つ目のルールがマッチするはず


def example_policy_chice():
    logger.info("start example_policy_choice")
    policy= ThresholdBestPolicy(threshold=50)
    content = "githubsを使ってバージョン管理を行いたい。"
    tool = ["git","svn","hg","bzr","cvs","github"]
    for key in tool:
        policy.add_rule_and_action(
            rule=IdentifierRule(ident=key),
            action=choice_action(key,f"choice_{key}"),
        )
                    
    decide =  policy.decide(ctx=content)
    print("decision:", decide)
    ret =  policy.run(ctx=content)
    print("action:", ret)
                

if __name__ == "__main__":
    # example_policy_first_match()
    # example_policy_all_match()
    # example_policy_threshold()
    # example_policy_threshold_filter()
    # example_policy_threshold_trigger()
    # example_policy_threshold_best()
    # example_policy_best_score()
    example_policy_chice()
    

