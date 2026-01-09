"""
ユーリティ関数(要約)
エージェントの要約機能を提供するモジュールです。
"""

from ..type.llm.llm_message import LLMMessage
from ..type.llm.llm_response import LLMResponse
from typing import List
from ..llm import LLMClientBase, LLMOpenAIClient


def summarize(messages: List[LLMMessage], llm_client: LLMClientBase = None) -> str:
    """
    Messageのリストを要約する関数

    Args:
        messages (List[LLMMessage]): 要約するメッセージのリスト
        llm_client (LLMClientBase): LLMクライアントのインスタンス
    """
    text = "\n".join([f"{m.role}: {m.content}" for m in messages])
    prompt = f"""以下の会話を簡潔に日本語で要約してください。

{text}"""
    if llm_client is None:
        config = {"max_tokens": 1000}
        llm_client = LLMOpenAIClient(temperature=0.2, config=config)
    response: LLMResponse = llm_client.request(
        prompt=prompt, system_prompt="あなたは要約エージェントです"
    )
    return f"要約すると以下の通りです。\n\n{response.get_message()}"
