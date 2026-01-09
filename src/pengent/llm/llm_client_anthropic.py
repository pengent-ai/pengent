import os
import requests
import json
from .llm_client_base import LLMClientBase, LLMResponse, LLMMessage
from ..type.llm.llm_message import LLMClientType
from ..type.llm.llm_response import LLMResponseTokenUsage


class LLMAnthropicClient(LLMClientBase):
    """
    Anthropic LLMクライアントクラス
    """

    def __init__(
        self,
        model_name="claude-haiku-4-5-20251001",
        temperature=0.0,
        config=None,
    ):
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
            llm_type=LLMClientType.ANTHROPIC.value,
        )
        # ANTHROPIC_API_KEYクライアントの初期化(環境変数から読み込み)
        self.__api_key = os.getenv("ANTHROPIC_API_KEY")
        self.version = self.config.get("version", "2023-06-01")
        self._type = LLMClientType.ANTHROPIC.value

    def request(self, prompt=None, messages: list = None, **kwargs):
        headers = {
            "x-api-key": self.__api_key,
            "anthropic-version": self.version,
            "content-type": "application/json",
        }

        if kwargs.get("system_prompt", False):
            system_prompt = kwargs.get("system_prompt")
        else:
            system_prompt = self.config.get("system_prompt", "")

        if messages:
            msg_temp = LLMMessage.to_format_messages(
                messages, LLMClientType.ANTHROPIC.value
            )
        elif prompt:
            msg_temp = [{"role": "user", "content": prompt.strip()}]
        else:
            raise ValueError("not set prompt.")

        # システムプロンプトを設定する
        kws = {}
        system_prompt = kwargs.get("system_prompt", self.system_prompt)
        if system_prompt:
            kws["system"] = system_prompt

        # Toolsを設定する
        tools: list[dict] = kwargs.get("tools", self.tools)
        if tools:
            # 整形する
            _tools = []
            for tool in tools:
                _function: dict = tool.get("function", {})
                parameters = _function.get("parameters", {})
                _tools.append(
                    {
                        "name": _function["name"],
                        "description": _function.get(
                            "description", "ツールの説明はありません"
                        ),
                        "input_schema": parameters,
                    }
                )
            kws["tools"] = _tools
            kws["tool_choice"] = {"type": "auto"}

        kws["max_tokens"] = self.config.get("max_tokens", 4096)

        is_web_search = kwargs.get("is_web_search", self.is_web_search)
        if is_web_search:
            web_search = {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 3,
            }
            if "tools" not in kws:
                kws["tools"] = [web_search]
            elif isinstance(kws["tools"], list):
                kws["tools"].append(web_search)

        payload = {
            "model": self.model_name,
            "messages": msg_temp,
            "temperature": self.temperature,
            **kws,
        }
        self.logger.debug(f"message: {json.dumps(msg_temp, ensure_ascii=False)[:500]}")

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
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
        # レスポンスの取得
        texts = []
        tools = []
        self.logger.debug(f"_parse_response result:\n {result}")
        llm_res = LLMResponse()
        llm_res.token_usage = LLMResponseTokenUsage(
            input_tokens=result["usage"]["input_tokens"],
            output_tokens=result["usage"]["output_tokens"],
            total_tokens=result["usage"]["input_tokens"]
            + result["usage"]["output_tokens"],
        )

        for item in result.get("content", []):
            if item.get("type") == "text":
                texts.append(item.get("text", ""))
            elif item.get("type") == "tool_use":
                tools.append(
                    {
                        "id": item["id"],
                        "type": "function",
                        "function": {
                            "name": item["name"],
                            "arguments": item["input"],
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

    def get_models(self, limit: int = 10):
        headers = {
            "x-api-key": self.__api_key,
            "anthropic-version": self.version,
        }
        params = {"limit": limit}
        resp = requests.get(
            "https://api.anthropic.com/v1/models",
            headers=headers,
            params=params,
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
        return [
            {"type": "Anthropic", "name": m["display_name"], "model": m["id"]}
            for m in data
        ]
