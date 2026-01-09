import json
from abc import ABC, abstractmethod
from ..lib import get_logger
from typing import Union, Type
from pydantic import BaseModel

from ..type.llm.llm_response import LLMResponse
from ..type.llm.llm_message import LLMMessage


class LLMClientBase(ABC):
    """
    LLMClientInクラスは、LLM(大規模言語モデル)クライアントのインターフェースを定義します。
    このクラスは、LLMクライアントの基本的な機能を提供するために設計されています。

    Notes:
        - model_name: 使用するLLMモデルの名前を指定
        - temperature: 生成されるテキストのランダム性や創造性の度合い
        - system_prompt: LLMに提供されるシステムプロンプトを指定
        - tools: LLMが使用できるツールや関数のリストを指定
        - is_web_search: LLMがWeb検索機能を使用するかどうか指定(対応モデルのみ)
        - response_schema: LLM応答のスキーマを指定します(対応モデルのみ)
    """

    def __init__(self, model_name, temperature=0.0, config=None, llm_type=""):
        """
        コンストラクタ
        Args:
            model_name (str): 使用するLLMモデルの名前
            temperature (float): 生成されるテキストのランダム性や創造性の度合い
            config (dict, optional): その他の設定オプション
            llm_type (str, optional): LLMのタイプを指定
        """
        if config is None:
            config = {}
        self.model_name = model_name
        self.temperature = temperature
        self.llm_type = llm_type
        self.config = config
        self.logger = get_logger()
        system_prompt = config.pop("system_prompt", None)
        self._system_prompt = system_prompt

    @property
    def system_prompt(self):
        return self._system_prompt
        # return self.config.get("system_prompt", None)

    @system_prompt.setter
    def system_prompt(self, value):
        self._system_prompt = value
        # self._system_prompt = value

    @property
    def is_web_search(self):
        return self.config.get("is_web_search", False)

    @is_web_search.setter
    def is_web_search(self, value: bool):
        self.config["is_web_search"] = value

    @property
    def tools(self):
        return self.config.get("tools", None)

    @tools.setter
    def tools(self, value):
        self.config["tools"] = value

    @property
    def response_schema(self) -> Union[dict, Type[BaseModel], None]:
        return self.config.get("response_schema", None)

    @response_schema.setter
    def response_schema(self, value: Union[dict, Type[BaseModel], None]):
        self.config["response_schema"] = value

    @abstractmethod
    def request(
        self, prompt: str = None, messages: LLMMessage = None, **kwargs
    ) -> LLMResponse:
        """
        LLMにリクエストを送信するメソッド

        Args:
            prompt (str): プロンプト
            messages (LLMMessage): メッセージのリスト
            kwargs: その他の引数
        """

    def _write_file(self, content):
        """
        レスポンスをファイルに書き込むメソッド
        :param file_path: ファイルパス
        :param content: 書き込む内容
        """
        output_file_path = self.config.get("output_file_path", "output.txt")
        with open(output_file_path, "w", encoding="utf-8") as file:
            file.write(content)

    def parse_json(self, text: str, fallback: dict = None) -> dict:
        """
        応答テキストをJSONとして安全にパースする
        :param text: LLMの出力
        :param fallback: パース失敗時の代替値
        :return: dict形式のデータ
        """
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parse error: {e}\ntext: {text}")
            if fallback is not None:
                return fallback
            raise ValueError("Invalid JSON response") from e

    def parse_tools(self, text: str) -> Union[list, None]:
        """
        応答テキストから tools を安全に抽出する
        :param text: LLMの出力(JSON形式が期待される)
        :return: toolsリスト または None(失敗時)
        """
        try:
            parsed = json.loads(text)
            if (
                isinstance(parsed, dict)
                and "tools" in parsed
                and isinstance(parsed["tools"], list)
            ):
                self.logger.debug(f"Parsed tools: {parsed['tools']}")
                # toolsがリストであることを確認
                return parsed["tools"]
            else:
                self.logger.warning(
                    "'tools' key not found or invalid format in parsed JSON."
                    f"\ntext: {text}"
                )
                return None
        except json.JSONDecodeError:
            self.logger.debug(f"parse_tools:not json response: text: {text}")
            return None
