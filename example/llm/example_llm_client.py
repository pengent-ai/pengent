import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
)

from pengent.lib import get_logger

logger = get_logger(level=10)

# envファイルを読み込む
from dotenv import load_dotenv
load_dotenv()

from pydantic import BaseModel
from pengent.llm import (
    LLMOpenAIClient,
    LLMAnthropicClient,
    LLMGeminiClient,
    LLMOpenRouterClient,
)
from pengent.type.llm.llm_message import LLMMessage
from pengent.llm.llm_client_gguf import LLMGGUFClient


class SampleResponseSchema(BaseModel):
    """サンプルのレスポンススキーマ"""
    question: str
    result: str


def example_opneai():
    llm_client = LLMOpenAIClient(
        model_name="gpt-5-mini",
        temperature=0.3,
        config={
            "is_output_file": False,
            "max_tokens": 200,
            "system_prompt": "\n".join(
                [
                    "あなたは優秀な窓口案内です。",
                    "わかりやすく、自然な日本語で丁寧に説明してください。",
                    "誤字や不自然な表現を避け、短めにまとめてください。",
                ]
            ),
        },
    )
    print(llm_client.request("富士山はどこの県にありますか？"))


def example_openai_web_search():
    llm_client = LLMOpenAIClient(
        model_name="gpt-5-mini",
        temperature=0.3,
        config={
            "is_output_file": False,
            "is_web_search": True,
            "system_prompt": "\n".join(
                [
                    "あなたは優秀な窓口案内です。",
                    "わかりやすく、自然な日本語で丁寧に説明してください。",
                    "誤字や不自然な表現を避け、短めにまとめてください。",
                ]
            ),
        },
    )
    print(llm_client.request("2025年の万博の開催地はどこですか？"))


def example_openai_json():
    llm_client = LLMOpenAIClient(
        model_name="gpt-5-mini",
        temperature=0.3,
        config={
            "is_output_file": False,
            "response_schema": SampleResponseSchema,
            "system_prompt": "\n".join(
                [
                    "あなたは優秀な窓口案内です。",
                    "わかりやすく、自然な日本語で丁寧に説明してください。",
                    "誤字や不自然な表現を避け、短めにまとめてください。",
                ]
            ),
        },
    )
    print(llm_client.request("富士山はどこの県にありますか？"))


def example_openai_continuous():
    llm_client = LLMOpenAIClient(
        model_name="gpt-5-mini",
        temperature=0.3,
        config={
            "is_output_file": False,
            "system_prompt": "\n".join(
                [
                    "あなたは優秀な窓口案内です。",
                    "わかりやすく、自然な日本語で丁寧に説明してください。",
                    "誤字や不自然な表現を避け、短めにまとめてください。",
                ]
            ),
        },
    )
    llm_messages:list[LLMMessage] = []
    llm_messages.append(
        LLMMessage.create_user_message("富士山はどこの県にありますか？")
    )
    res = llm_client.request(messages=llm_messages)
    print(res.content)
    llm_messages.append(
        LLMMessage.create_assistant_message(res.content)
    )
    print(llm_messages)
    llm_messages.append(
        LLMMessage.create_user_message("では、その近くの有名な観光地は？")
    )
    res2 = llm_client.request(messages=llm_messages)
    print(res2.content)



def example_anthropic():
    llm_client = LLMAnthropicClient(
        model_name="claude-3-5-haiku-20241022",
        temperature=0.3,
        config={
            "is_output_file": False,
            "system_prompt": "\n".join(
                [
                    "あなたは優秀な窓口案内です。",
                    "わかりやすく、自然な日本語で丁寧に説明してください。",
                    "誤字や不自然な表現を避け、短めにまとめてください。",
                ]
            ),
        },
    )
    print(llm_client.request("富士山はどこの県にありますか？"))


def example_anthropic_web_search():
    llm_client = LLMAnthropicClient(
        temperature=0.3,
        config={
            "is_output_file": False,
            "is_web_search": True,
            "system_prompt": "\n".join(
                [
                    "あなたは優秀な窓口案内です。",
                    "わかりやすく、自然な日本語で丁寧に説明してください。",
                    "誤字や不自然な表現を避け、短めにまとめてください。",
                ]
            ),
        },
    )
    print(llm_client.request("2025年の万博の開催地はどこですか？"))


def example_anthropic_json():
    llm_client = LLMAnthropicClient(
        temperature=0.3,
        config={
            "is_output_file": False,
            "response_schema": SampleResponseSchema,
            "system_prompt": "\n".join(
                [
                    "あなたは優秀な窓口案内です。",
                    "わかりやすく、自然な日本語で丁寧に説明してください。",
                    "誤字や不自然な表現を避け、短めにまとめてください。",
                    "JSON形式で返答してください。",
                ]
            ),
        },
    )
    print(llm_client.request("富士山はどこの県にありますか？"))

def example_anthropic_continuous():
    llm_client = LLMAnthropicClient(
        temperature=0.3,
        config={
            "is_output_file": False,
            "system_prompt": "\n".join(
                [
                    "あなたは優秀な窓口案内です。",
                    "わかりやすく、自然な日本語で丁寧に説明してください。",
                    "誤字や不自然な表現を避け、短めにまとめてください。",
                ]
            ),
        },
    )
    llm_messages:list[LLMMessage] = []
    llm_messages.append(
        LLMMessage.create_user_message("富士山はどこの県にありますか？")
    )
    res = llm_client.request(messages=llm_messages)
    print(res.content)
    llm_messages.append(
        LLMMessage.create_assistant_message(res.content)
    )
    print(llm_messages)
    llm_messages.append(
        LLMMessage.create_user_message("では、その近くの有名な観光地は？")
    )
    res2 = llm_client.request(messages=llm_messages)
    print(res2.content)


def example_gemini():
    # model_name="gemini-2.5-pro",
    llm_client = LLMGeminiClient(
        model_name="gemini-2.5-flash-lite",
        temperature=0.3,
        config={
            "is_output_file": False,
            "system_prompt": "\n".join(
                [
                    "あなたは優秀な窓口案内です。",
                    "わかりやすく、自然な日本語で丁寧に説明してください。",
                    "誤字や不自然な表現を避け、短めにまとめてください。",
                ]
            ),
        },
    )
    res = llm_client.request(prompt="富士山はどこの県にありますか？")
    print(res.content)


def example_gemini_web_search():
    # model_name="gemini-2.5-pro",
    llm_client = LLMGeminiClient(
        model_name="gemini-2.5-flash-lite",
        temperature=0.3,
        config={
            "is_output_file": False,
            "is_web_search": True,
            "system_prompt": "\n".join(
                [
                    "あなたは優秀な窓口案内です。",
                    "わかりやすく、自然な日本語で丁寧に説明してください。",
                    "誤字や不自然な表現を避け、短めにまとめてください。",
                ]
            ),
        },
    )
    print(llm_client.request("2025年の万博の開催地はどこですか？"))


def example_gemini_json():
    llm_client = LLMGeminiClient(
        model_name="gemini-2.5-flash",
        temperature=0.3,
        config={
            "is_output_file": False,
            "response_schema": SampleResponseSchema,
            "system_prompt": "\n".join(
                [
                    "あなたは優秀な窓口案内です。",
                    "わかりやすく、自然な日本語で丁寧に説明してください。",
                    "誤字や不自然な表現を避け、短めにまとめてください。",
                ]
            ),
        },
    )
    print(llm_client.request("富士山はどこの県にありますか？"))


def example_gemini_continuous():
    llm_client = LLMGeminiClient(
        model_name="gemini-2.5-flash-lite",
        temperature=0.3,
        config={
            "is_output_file": False,
            "system_prompt": "\n".join(
                [
                    "あなたは優秀な窓口案内です。",
                    "わかりやすく、自然な日本語で丁寧に説明してください。",
                    "誤字や不自然な表現を避け、短めにまとめてください。",
                ]
            ),
        },
    )
    llm_messages:list[LLMMessage] = []
    llm_messages.append(
        LLMMessage.create_user_message("富士山はどこの県にありますか？")
    )
    res = llm_client.request(messages=llm_messages)
    print(res.content)
    llm_messages.append(
        LLMMessage.create_assistant_message(res.content)
    )
    print(llm_messages)
    llm_messages.append(
        LLMMessage.create_user_message("では、その近くの有名な観光地は？")
    )
    res2 = llm_client.request(messages=llm_messages)
    print(res2.content)



def example_open_router():
    print("example")
    llm_client = LLMOpenRouterClient(
        model_name="mistralai/mistral-small-3.1-24b-instruct:free",
        temperature=0.3,
        config={
            "is_output_file": False,
            "max_tokens": 1024,
            "system_prompt": """
            あなたは優秀な窓口案内です。
            わかりやすく、自然な日本語で丁寧に説明してください。
            誤字や不自然な表現を避け、短めにまとめてください。
            """,
        },
    )
    res = llm_client.request(prompt="富士山はどこの県にありますか？")
    print(res.content)


def example_gguf():
    print("example")
    llm_client = LLMGGUFClient(
         # modelは各自で用意してください
        model_name="qwen1_5-1.8b-chat.Q4_K_M.gguf",
        temperature=0.3,
        config={
            "is_output_file": False,
            "is_auto_setup": True,
            "max_tokens": 50,
            "system_prompt": """
            あなたは優秀な窓口案内です。
            わかりやすく、自然な日本語で丁寧に説明してください。
            誤字や不自然な表現を避け、10文字で返してください。
            """,
        },
    )
    print(llm_client.request("富士山はどこの県にありますか？"))




if __name__ == "__main__":
    # example_opneai()
    # example_openai_web_search()
    # example_openai_json()
    # example_openai_continuous()

    # example_anthropic()
    # example_anthropic_web_search()
    # example_anthropic_json()
    # example_anthropic_continuous()
    
    # example_gemini()
    # example_gemini_web_search()
    # example_gemini_json()
    example_gemini_continuous()
    
    # example_open_router()
    # example_gguf()
