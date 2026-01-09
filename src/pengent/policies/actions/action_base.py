import random
from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class Action:
    """アクションの基底クラス"""

    name: str
    fn: Callable[[Any, Any], Any]
    description: str = ""
    enabled: bool = True

    def __call__(self, ctx: Any = None, decision: Any = None) -> Any:
        """アクションを実行する

        Args:
            ctx: コンテキスト情報
            decision: ポリシーの判定結果

        Returns:
            アクションの実行結果
        """
        if not self.enabled:
            return None
        return self.fn(ctx, decision)


def greet_action(locale: str = "ja") -> Action:
    """
    挨拶を行うアクション(お試し用)
    """

    def _greet(ctx: Any = None, decision: Any = None) -> str:
        if locale == "ja":
            greetings = [
                "こんにちは！今日はどのようにお手伝いできますか？",
                "やあ！何かお手伝いできることはありますか？",
                "こんにちは！どのようにお手伝いできますか？",
            ]
        elif locale == "en":
            greetings = [
                "Hello! How can I assist you today?",
                "Hi there! What can I do for you?",
                "Greetings! How may I help you?",
            ]
        else:
            raise ValueError(
                "Unsupported language. Supported languages are 'ja' and 'en'."
            )

        message = random.choice(greetings)
        return message

    return Action(
        name="greet",
        fn=_greet,
        description=f"Greeting action (locale={locale})",
    )


def choice_action(value: Any, name: str = "", description: str = "") -> Action:
    def _fn(ctx: Any = None, decision: Any = None) -> Any:
        return value

    return Action(
        name=name if name else "choice",
        fn=_fn,
        description=description or f"Return fixed value: {value!r}",
    )
