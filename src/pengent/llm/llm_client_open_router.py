import os
import requests
import json
from .llm_client_base import LLMClientBase, LLMResponse, LLMMessage
from ..type.llm.llm_message import LLMClientType
from ..type.llm.llm_response import LLMResponseTokenUsage

# Prompt Training Allowed
# mistralai/mistral-7b-instruct:free
# https://openrouter.ai/settings/privacy にアクセスし、
# 「prompt training」オプションを有効にする必要がある、
# shisa-ai/shisa-v2-llama3.3-70b:free


class LLMOpenRouterClient(LLMClientBase):
    """
    Anthropic LLMクライアントクラス
    """

    def __init__(
        self,
        model_name="mistralai/mistral-small-3.1-24b-instruct:free",
        temperature=0.0,
        config=None,
    ):
        """
        コンストラクタ

        Args:
            model_name (str): 使用するLLMモデルの名前
            temperature (float): 生成されるテキストのランダム性や創造性の度合い
            config (dict, optional): その他の設定オプション
        """
        super().__init__(
            model_name,
            temperature,
            config,
            llm_type=LLMClientType.OPENROUTER.value,
        )
        # OpenRouterクライアントの初期化(環境変数から読み込み)
        self.__api_key = os.getenv("OPEN_ROUTER_API_KEY")

    def set_token(self, token):
        self.__api_key = token

    def request(self, prompt=None, messages: list = None, **kwargs):
        """
        LLMにリクエストを送信するメソッド
        :param prompt: プロンプト
        :param kwargs: その他の引数
        :return: レスポンス
        """
        if messages:
            msg_temp = LLMMessage.to_format_messages(messages)
        elif prompt:
            msg_temp = [{"role": "user", "content": prompt.strip()}]
        else:
            raise ValueError("not set prompt.")

        # システムプロンプトを設定する
        system_prompt = kwargs.get("system_prompt", self.system_prompt)
        if system_prompt:
            msg_temp.insert(0, {"role": "system", "content": system_prompt})

        payload = {
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.config.get("max_tokens", 3000),
            "messages": msg_temp,
        }
        tools = kwargs.get("tools", self.tools)
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        self.logger.debug(f"message: {json.dumps(payload, ensure_ascii=False)[:500]}")

        headers = {
            "Authorization": f"Bearer {self.__api_key}",
            "content-type": "application/json",
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        result = response.json()
        # レスポンスの取得
        return self._parse_response(result)

    def _parse_response(self, result) -> LLMResponse:
        """
        レスポンスを解析するメソッド
        :return: 解析されたレスポンス
        """
        self.logger.debug(f"_parse_response result:\n {result}")

        llm_res = LLMResponse()
        llm_res.token_usage = LLMResponseTokenUsage(
            input_tokens=result["usage"]["prompt_tokens"],
            output_tokens=result["usage"]["completion_tokens"],
            total_tokens=result["usage"]["total_tokens"],
        )

        tools = []
        if result["choices"][0]["message"].get("content"):
            llm_res.add_content_text(result["choices"][0]["message"].get("content"))
            if self.config.get("is_output_file", False):
                # レスポンスをファイルに書き込む
                self._write_file(result["choices"][0]["message"]["content"])

        if result["choices"][0]["message"].get("tool_calls"):
            tools_calls: list[dict] = result["choices"][0]["message"]["tool_calls"]
            for tool_call in tools_calls:
                _function: dict = tool_call.get("function")
                tools.append(
                    {
                        "id": tool_call.get("id"),
                        "type": "function",
                        "function": {
                            "name": _function.get("name"),
                            "arguments": _parse_tool_arguments(
                                _function.get("arguments")
                            ),
                        },
                    }
                )
            print(f"tools:{tools}")
            llm_res.add_content_tools(tools)

        return llm_res

    def search_model(self, category: str = None, limit=100) -> list:
        """
        検索を行うメソッド
        :param category: 検索クエリ
        :return: 検索結果

        Notes:
            - モデルIDに付加のバリアント識別子により一部の挙動が変化します。
            - `mistralai/mistral-7b-instruct:free`は無料のバリアントを示す。
        """
        url = "https://openrouter.ai/api/v1/models"
        headers = {
            "Authorization": f"Bearer {self.__api_key}",
        }
        params = {
            "limit": limit,
        }
        if category:
            params["category"] = category
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        self.logger.debug(f"search_model result:\n {result}")
        models = []
        for model in result.get("data", []):
            models.append(
                {
                    "type": LLMClientType.OPENROUTER.value,
                    "name": model["id"],
                    "model": model["id"],
                    "description": model.get("description", ""),
                    "category": model.get("category", ""),
                    "provider": model.get("provider", ""),
                    "is_free": model.get("is_free", False),
                }
            )

        return models


def _parse_tool_arguments(arg_str: str) -> dict:
    """JSON形式がおかしい場合でも復元を試みるツール引数のパース"""
    s = (arg_str or "").strip()
    decoder = json.JSONDecoder()

    objs = []
    i = 0
    while i < len(s):
        # 次のJSON開始を探す
        j = s.find("{", i)
        if j < 0:
            break
        try:
            obj, end = decoder.raw_decode(s, j)
            if isinstance(obj, dict):
                objs.append(obj)
            i = end
        except json.JSONDecodeError:
            i = j + 1

    if not objs:
        raise ValueError(f"Invalid tool arguments: {arg_str!r}")

    # 末尾のdictを採用(今回の {}{"query":"Tokyo"} なら後者が残る)
    return objs[-1]
