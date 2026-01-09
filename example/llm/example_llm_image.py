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

from pengent.llm import (
    LLMOpenAIClient,
    LLMAnthropicClient,
    LLMGeminiClient,
)
from pengent.type.llm.llm_message import LLMMessage, LLMMessageContent


def example_opneai_image_url():
    llm_client = LLMOpenAIClient(
        model_name="gpt-5-mini",
        temperature=0.3,
        config={
            "max_tokens": 200,
            "system_prompt": "\n".join(
                [
                    "画像を送ります。画像の内容を説明してください。",
                ]
            ),
        },
    )

    content = [
        LLMMessageContent.create_text_content("この画像はなんの画像ですか？"),
        LLMMessageContent.create_image_url(
            url="https://placehold.jp/150x150.png"
        ),
    ]
    messages = [LLMMessage.create_user_message(content=content)]
    print(llm_client.request(messages=messages))


def example_opneai_image_base64():
    llm_client = LLMOpenAIClient(
        model_name="gpt-5-mini",
        temperature=0.3,
        config={
            "max_tokens": 200,
            "system_prompt": "\n".join(
                [
                    "画像を送ります。画像の内容を説明してください。",
                ]
            ),
        },
    )

    content = [
        LLMMessageContent.create_text_content("この画像はなんの画像ですか？"),
        LLMMessageContent.create_image_from_file("example/utility/sample_data/sample.png"),
     ]
    messages = [LLMMessage.create_user_message(content=content)]
    print(llm_client.request(messages=messages))

def example_anthropic_image_url():
    llm_client = LLMAnthropicClient(
        temperature=0.3,
        config={
            "max_tokens": 200,
            "system_prompt": "\n".join(
                [
                    "画像を送ります。画像の内容を説明してください。",
                ]
            ),
        },
    )

    content = [
        LLMMessageContent.create_text_content("この画像はなんの画像ですか？"),
        LLMMessageContent.create_image_url(
            url="https://placehold.jp/150x150.png"
        ),
    ]
    messages = [LLMMessage.create_user_message(content=content)]
    print(llm_client.request(messages=messages))


def example_anthropic_image_base64():
    llm_client = LLMAnthropicClient(
        temperature=0.3,
        config={
            "max_tokens": 200,
            "system_prompt": "\n".join(
                [
                    "画像を送ります。画像の内容を説明してください。",
                ]
            ),
        },
    )

    content = [
        LLMMessageContent.create_text_content("この画像はなんの画像ですか？"),
        LLMMessageContent.create_image_from_file("example/utility/sample_data/sample.png"),
     ]
    messages = [LLMMessage.create_user_message(content=content)]
    msgs = LLMMessage.to_format_messages(messages, llm_type="anthropic")
    import json
    print(f"{json.dumps(msgs,ensure_ascii=False)[:200]}")
    print(llm_client.request(messages=messages))

def example_gemini_image_url():
    llm_client = LLMGeminiClient(
        temperature=0.3,
        config={
            "max_tokens": 500,
            "system_prompt": "\n".join(
                [
                    "画像を送ります。画像の内容を説明してください。",
                ]
            ),
        },
    )

    content = [
        LLMMessageContent.create_text_content("この画像はなんの画像ですか？"),
        LLMMessageContent.create_image_url(
            url="https://placehold.jp/150x150.png"
        ),
    ]
    messages = [LLMMessage.create_user_message(content=content)]
    print(llm_client.request(messages=messages))

def example_gemini_image_base64():
    llm_client = LLMGeminiClient(
        temperature=0.3,
        config={
            "max_tokens": 500,
            "system_prompt": "\n".join(
                [
                    "画像を送ります。画像の内容を説明してください。",
                ]
            ),
        },
    )

    content = [
        LLMMessageContent.create_text_content("この画像はなんの画像ですか？"),
        LLMMessageContent.create_image_from_file("example/utility/sample_data/sample.png"),
     ]
    messages = [LLMMessage.create_user_message(content=content)]
    print(llm_client.request(messages=messages))



if __name__ == "__main__":
    # example_opneai_image_url()
    # example_opneai_image_base64()
    # example_anthropic_image_url()
    # example_anthropic_image_base64()
    # example_gemini_image_url()
    example_gemini_image_base64()
