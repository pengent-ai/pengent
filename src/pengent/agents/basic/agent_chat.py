from ..agent_base import AgentBase
from ...llm import LLMOpenRouterClient, LLMClientBase


class AgentChat(AgentBase):
    """
    AI Agent Chat(雑談特化エージェント)クラス

        Features:
            - ユーザーとの自然な会話・軽い質問対応をする
            - ユーザーとお話ししながら、必要な情報を記録する

        Parameters:
            - prior_info (dict): 事前の情報
              - (例:`{"職業": "エンジニア", "趣味": "読書"})`
    """

    def __init__(self, llm_client: LLMClientBase = None, params: dict = None):
        """
        コンストラクタ
        """
        if llm_client is None:
            config = {"max_tokens": 1000}
            llm_client = LLMOpenRouterClient(temperature=0.5, config=config)
        if params is None:
            params = {
                "role": (
                    "You are a friendly and engaging AI "
                    "that enjoys natural conversation with the user."
                ),
                "goal": (
                    "Have a light, natural conversation with the user. "
                    "You can ask questions in return to continue the chat."
                ),
                "constraints": [
                    "出力は文字列形式とする",
                    "返答は丁寧で自然な日本語にすること",
                    "絵文字は使わないこと",
                    "特にトピックが指定されていない場合は、会話を広げるための質問をすること",
                ],
            }
        super().__init__("雑談エージェント", llm_client, params)
