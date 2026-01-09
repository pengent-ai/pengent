from .llm_client_base import LLMClientBase
from .llm_client_openai import LLMOpenAIClient
from .llm_client_anthropic import LLMAnthropicClient
from .llm_client_open_router import LLMOpenRouterClient
from .llm_client_gemini import LLMGeminiClient


class LLMClientFactory:
    """
    LLMクライアントファクトリークラス
    """

    @staticmethod
    def create(client_type: str, **kwargs) -> LLMClientBase:
        """
        LLMクライアントを生成するメソッド
        :param client_type: クライアントの種類
        :param kwargs: その他の引数
        :return: LLMクライアントインスタンス
        """
        if client_type == "openai":
            return LLMOpenAIClient(**kwargs)
        elif client_type == "anthropic":
            return LLMAnthropicClient(**kwargs)
        elif client_type == "open_router":
            return LLMOpenRouterClient(**kwargs)
        elif client_type == "gemini":
            return LLMGeminiClient(**kwargs)
        elif client_type == "gguf":
            from .llm_client_gguf import LLMGGUFClient

            return LLMGGUFClient(**kwargs)
        else:
            raise ValueError(f"Unknown client type: {client_type}")

    @staticmethod
    def create_from_model(model_name: str, **kwargs) -> LLMClientBase:
        if model_name in [
            "gpt-5-mini",
            "gpt-4.1-mini",
            "gpt-4.1",
            "gpt-4o",
            "gpt-4",
        ]:
            return LLMOpenAIClient(model_name=model_name, **kwargs)
        elif model_name in [
            "claude-3-5-haiku-20241022",
            "claude-sonnet-4-20250514",
            "claude-opus-4-20250514",
        ]:
            return LLMAnthropicClient(model_name=model_name, **kwargs)
        elif model_name in [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
        ]:
            return LLMGeminiClient(model_name=model_name, **kwargs)
        elif model_name in [
            "mistralai/mistral-7b-instruct:free",
            "mistralai/mistral-small-3.1-24b-instruct:free",
            "shisa-ai/shisa-v2-llama3.3-70b:free",
            "deepseek/deepseek-chat-v3-0324:free",
        ]:
            return LLMOpenRouterClient(model_name=model_name, **kwargs)
        else:
            raise ValueError(f"Unknown model name: {model_name}")
