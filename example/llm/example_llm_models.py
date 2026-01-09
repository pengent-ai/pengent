import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
)

from pengent.lib import get_logger

logger = get_logger(level=10)

from dotenv import load_dotenv
from pengent.llm import LLMOpenRouterClient

# envファイルを読み込む
load_dotenv()


def example_models():
    # llm_client = LLMOpenAIClient()
    # models = llm_client.get_models(20)
    # logger.info(f"OpenAI Models: {models}")

    # llm_client = LLMAnthropicClient()
    # models = llm_client.get_models(limit=5)
    # logger.info(f"Anthropic Models: {models}")

    # llm_client = LLMGeminiClient()
    # models = llm_client.get_models(limit=None)
    # logger.info(f"Gemini Models: {models}")

    llm_client = LLMOpenRouterClient()
    models = llm_client.search_model()
    logger.info(f"OpenRouter Models: {models}")


if __name__ == "__main__":
    example_models()
