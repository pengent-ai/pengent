import os
import json
import requests
import inspect
from .llm_client_base import LLMClientBase, LLMResponse, LLMMessage, BaseModel
from ..type.llm.llm_message import LLMClientType
from ..type.llm.llm_response import LLMResponseTokenUsage


# Generative Language API
# GEMINI_API_KEYが必要
# URL: https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent
# APIキー認証


class LLMGeminiClient(LLMClientBase):
    """
    Gemini LLMクライアントクラス
    """

    def __init__(self, model_name="gemini-2.5-flash", temperature=0.0, config=None):
        """
        コンストラクタ

        Args:
            model_name (str): モデル名
            temperature (float): 温度パラメータ
            config (dict): その他の設定
        """
        super().__init__(
            model_name,
            temperature,
            config,
            llm_type=LLMClientType.GEMINI.value,
        )
        self.__api_key = os.getenv("GEMINI_API_KEY")

    def set_token(self, token):
        self.__api_key = token

    def request(self, prompt=None, messages: list[LLMMessage] = None, **kwargs):
        if messages:
            msg_temp = LLMMessage.to_format_messages(
                messages, LLMClientType.GEMINI.value
            )
        elif prompt:
            msg_temp = [{"role": "user", "parts": [{"text": prompt.strip()}]}]
        else:
            raise ValueError("not set prompt.")

        # システムプロンプトを設定する
        system_prompt = kwargs.get("system_prompt", self.system_prompt)
        if system_prompt:
            msg_temp.insert(
                0, {"role": "user", "parts": [{"text": system_prompt.strip()}]}
            )

        headers = {"Content-Type": "application/json"}
        params = {"key": self.__api_key}
        payload = {
            "contents": msg_temp,
            "generationConfig": {
                "temperature": self.temperature,
            },
        }
        if self.config.get("max_tokens", None):
            payload["generationConfig"]["maxOutputTokens"] = self.config.get(
                "max_tokens", None
            )

        if self.response_schema:
            if self.model_name not in ["gemini-2.5-flash"]:
                ValueError("Response Json Format is not supported for this model.")

            self.logger.debug(f"response_schema: {self.response_schema}")

            payload["generationConfig"]["responseMimeType"] = "application/json"
            if inspect.isclass(self.response_schema) and issubclass(
                self.response_schema, BaseModel
            ):
                self.logger.debug(
                    "response_schema model_json_schema: "
                    f"{self.response_schema.model_json_schema()}"
                )
                payload["generationConfig"]["responseSchema"] = (
                    self.response_schema.model_json_schema()
                )
            elif isinstance(self.response_schema, dict):
                payload["generationConfig"]["responseSchema"] = self.response_schema

        # Toolsを設定する
        tools: list[dict] = kwargs.get("tools", self.tools)
        if tools:
            # 整形する
            _tools = []
            for tool in tools:
                _function: dict = tool.get("function", {})
                parameters = _function.get("parameters", {})
                if isinstance(parameters, dict):
                    # additionalPropertiesを除去
                    parameters = {
                        k: v
                        for k, v in parameters.items()
                        if k != "additionalProperties"
                    }
                _function["parameters"] = parameters
                _tools.append(_function)

            payload["tools"] = {}
            payload["tools"]["function_declarations"] = _tools

        is_web_search = kwargs.get("is_web_search", self.is_web_search)
        if is_web_search:
            # google_search(1.5系なら {"google_search_retrieval": {...}})
            web_search = {"google_search": {}}
            if "tools" not in payload:
                payload["tools"] = [web_search]
            elif isinstance(payload["tools"], list):
                payload["tools"].append(web_search)

        # リクエストのエンドポイント
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
        self.logger.debug(f"message: {json.dumps(payload, ensure_ascii=False)[:3000]}")
        response = requests.post(endpoint, headers=headers, params=params, json=payload)
        response.raise_for_status()
        result = response.json()
        # レスポンスの取得
        return self._parse_response(result)

    def _parse_response(self, result) -> LLMResponse:
        """
        レスポンスを解析するメソッド
        :return: 解析されたレスポンス
        """
        # レスポンスの取得
        texts = []
        tools = []
        self.logger.debug(f"_parse_response result:\n {result}")
        llm_res = LLMResponse()
        llm_res.token_usage = LLMResponseTokenUsage(
            input_tokens=result["usageMetadata"].get("promptTokenCount", 0),
            output_tokens=result["usageMetadata"].get("candidatesTokenCount", 0),
            total_tokens=result["usageMetadata"].get("totalTokens", 0),
        )

        # candidatesを取得
        candidates = result.get("candidates", [])
        if not candidates:
            raise ValueError("candidatesが空です")

        # 最初の候補を取る(普通は1個)
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        # partsを順番に読む
        for item in parts:
            if "text" in item:
                texts.append(item["text"])
                if self.response_schema:
                    # JSONレスポンスとしてパース
                    if inspect.isclass(self.response_schema) and issubclass(
                        self.response_schema, BaseModel
                    ):
                        obj = self.response_schema.model_validate_json(item["text"])
                        llm_res.add_content_object(obj)
                    elif isinstance(self.response_schema, dict):
                        obj = self.parse_json(item["text"])
                        llm_res.add_content_object(obj)

            elif "functionCall" in item:
                tools.append(
                    {
                        "id": item["functionCall"]["name"],
                        "type": "function",
                        "function": {
                            "name": item["functionCall"]["name"],
                            "arguments": item["functionCall"]["args"],
                        },
                    }
                )

        if texts:
            texts = "\n".join(texts).strip()
            llm_res.add_content_text(texts)
            if self.config.get("is_output_file", False):
                self._write_file(texts)

        if tools:
            llm_res.add_content_tools(tools)

        return llm_res

    def _write_file(self, content: str):
        with open("gemini_output.txt", "w", encoding="utf-8") as f:
            f.write(content)

    def get_models(self, limit: int = 10):
        endpoint = "https://generativelanguage.googleapis.com/v1beta/models"
        params = {
            "key": self.__api_key,
            "pageSize": limit,
            # "orderBy": "createTime desc",
        }
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        models = response.json().get("models", [])
        model_list = [
            {
                "type": "gemini",
                "name": model["name"],
                "model": model["name"],
            }
            for model in models[:limit]
        ]
        return model_list
