from pengent.llm.llm_client_base import LLMClientBase
from pengent.type.llm.llm_message import LLMMessage
from pengent.type.llm.llm_response import (
    LLMResponse,
    LLMResponseTokenUsage,
    ResponseText,
)


class MockLLMClient(LLMClientBase):
    """LLMのモッククライアントクラス"""

    def request(
        self, prompt=None, messages: LLMMessage = None, **kwargs
    ) -> LLMResponse:
        return LLMResponse(
            content=[
                ResponseText(text="Hello, world! LLM Mock"),
            ],
            token_usage=LLMResponseTokenUsage(
                input_tokens=10,
                output_tokens=5,
                total_tokens=15,
            ),
        )
