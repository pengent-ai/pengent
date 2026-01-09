import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
)
from pengent.policies.rules import (
    KeywordRule,
    KeywordAdvancedRule,
    JapaneseIntentRule,
)


from pengent.lib import get_logger
logger = get_logger(level=10)

def example_rule_keyword():
    logger.info("Testing KeywordRule")
    ctx = "hello world"
    rule = KeywordRule("hello", score=5)
    print(rule.dump(ctx))

def example_rule_keyword_advanced():
    logger.info("Testing KeywordAdvancedRule")
    ctx = "hello world, goodbye"
    rule = KeywordAdvancedRule(
        any_groups=[["hello", "hi"], ["world", "earth"]],
        required_all=["bye"],
        forbidden_any=["error", "fail"],
        score=10,
        normalize=True,
    )
    print(rule.dump(ctx))

def example_rule_japanese_intent():
    logger.info("Testing JapaneseIntentRule")
    ctx = "私はリンゴを食べたいです。"
    rule = JapaneseIntentRule(
        subject_keywords=["リンゴ", "果物"],
        verb_keywords=["食べる", "食べたい"],
        context_window=1,
        normalize=True,
    )
    print(rule.dump(ctx))


if __name__ == "__main__":
    # example_rule_keyword()
    # example_rule_keyword_advanced()
    example_rule_japanese_intent()
