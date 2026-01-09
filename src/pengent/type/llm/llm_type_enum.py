from enum import Enum


class LLMClientType(str, Enum):
    """
    LLMクライアントの種類を表す列挙型
    """

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENROUTER = "open_router"
    GGUF = "gguf"

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


class LLMMessageRole(str, Enum):
    """
    LLMメッセージの役割を表す列挙型
    """

    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

    def format(self, llm_type: str = LLMClientType.OPENAI.value) -> str:
        if llm_type == LLMClientType.ANTHROPIC.value and self == LLMMessageRole.TOOL:
            return "user"
        elif (
            llm_type == LLMClientType.GEMINI.value and self == LLMMessageRole.ASSISTANT
        ):
            return "model"
        elif llm_type == LLMClientType.GEMINI.value and self == LLMMessageRole.TOOL:
            return "function"
        else:
            return self.value

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value
