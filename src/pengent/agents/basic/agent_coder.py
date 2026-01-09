from ..agent_base import AgentBase
from ...llm import LLMOpenAIClient, LLMClientBase


class AgentCoder(AgentBase):
    """
    AI Agent Coder(コード生成エージェント・スニペット用)クラス

        Features:
            - ユーザーの要望に応じた短いコードスニペットを作成します
            - Gitリポジトリからファイルを取得し、コード生成に活用します
            - 簡易的なコードに関して単一的なファイルの生成と解析を行います
            - 必要があればコードの実行結果を確認し、必要に応じて修正します
            - 必要に応じてヒントとコードの説明やコメントを追加します

        Parameters:
            - prior_info (dict): 事前情報
                (例: {"フレームワーク": "Flask", "用途": "簡単なWebAPI作成"})
    """

    def __init__(self, llm_client: LLMClientBase = None, params: dict = None):
        """
        コンストラクタ
        """
        if llm_client is None:
            config = {
                "is_output_file": False,
            }
            llm_client = LLMOpenAIClient(temperature=0.2, config=config)
        if params is None:
            params = {
                "role": (
                    "You are a skilled coder AI that generates short,"
                    " functional code snippets in response to user requests."
                ),
                "goal": (
                    "Generate short and functional code snippets"
                    " according to user requests."
                ),
                "constraints": [
                    "「単一ファイル」「短く簡潔なスニペット」生成と「単一ファイル」の解析を対象としています",
                    "複数ファイルにまたがる実装、設計指針に基づく構造化コード、アーキテクチャ設計などには対応していません",
                    "複雑な実装には別の構造化コード専用エージェント(AgentProgrammer)を使用してください",
                    "必要に応じてソースコードを実行すること",
                    "特に言語指定がなければPythonで作成すること",
                ],
            }
        super().__init__("スニペット用コーディング特化エージェント", llm_client, params)
        self.set_tools(tabs=["coder"])
