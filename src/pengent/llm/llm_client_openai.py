import os
import json
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.responses import (
    ResponseOutputMessage,
    ResponseOutputText,
    Response as OpenAIResponse,
)
from .llm_client_base import LLMClientBase, LLMResponse, LLMMessage
from ..type.llm.llm_message import LLMClientType
from ..type.llm.llm_response import LLMResponseTokenUsage


class LLMOpenAIClient(LLMClientBase):
    """
    OpenAI LLMクライアントクラス
    """

    def __init__(self, model_name="gpt-5-mini", temperature=0.0, config=None):
        super().__init__(
            model_name,
            temperature,
            config,
            llm_type=LLMClientType.OPENAI.value,
        )
        # OpenAIクライアントの初期化(環境変数から読み込み)
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        self._type = LLMClientType.OPENAI.value

    def request(
        self, prompt=None, messages: list[LLMMessage] = None, **kwargs
    ) -> LLMResponse:
        """OpenAIへのリクエストを送信する

        Notes:
            画像対応:
              - 画像URL,base64, Files API( 先アップロード:multipart/form-data)


        """
        if messages:
            msg_temp = LLMMessage.to_format_messages(
                messages, LLMClientType.OPENAI.value
            )
        elif prompt:
            msg_temp = [{"role": "user", "content": prompt.strip()}]
        else:
            raise ValueError("not set prompt.")

        # システムプロンプトを設定する
        system_prompt = kwargs.get("system_prompt", self.system_prompt)
        if system_prompt:
            msg_temp.insert(0, {"role": "system", "content": system_prompt})

        self.logger.debug(f"message: {json.dumps(msg_temp, ensure_ascii=False)[:500]}")

        # Toolsを設定する
        tools = kwargs.get("tools", self.tools)
        kws = {}

        if tools:
            kws["tools"] = tools
            kws["tool_choice"] = "auto"

        is_web_search = kwargs.get("is_web_search", self.is_web_search)
        if is_web_search:
            web_search = {"type": "web_search"}
            if "tools" not in kws:
                kws["tools"] = [web_search]
            elif isinstance(kws["tools"], list):
                kws["tools"].append(web_search)

            resp: OpenAIResponse = self.client.responses.create(
                model=self.model_name if self.model_name else "gpt-4o",
                input=msg_temp,  # messages配列をそのまま渡せます
                tools=kws.get("tools"),
                tool_choice="auto",
            )
            return self._parse_api_response(resp)

        # Chat Completions-> Responses APIに寄せる
        if self.response_schema:
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "SampleResponseSchema",
                    "schema": self.response_schema.model_json_schema(),
                    "strict": False,
                },
            }
            kws["response_format"] = response_format

        # self.config.get("response_format")
        #     self.client.beta.chat.completions.parse()を使わないとならない

        if self.model_name in ["gpt-5-mini", "gpt-5"]:
            # gpt-5-miniはtemperature、max_tokensをサポートしない
            response = self.client.chat.completions.create(
                model=self.model_name, messages=msg_temp, **kws
            )
        else:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=msg_temp,
                temperature=self.temperature,
                max_tokens=self.config.get("max_tokens", None),
                **kws,
            )
        return self._parse_response(response)

    def _parse_api_response(self, response: OpenAIResponse):
        self.logger.debug(f"_parse_api_response response:\n {response}")
        llm_res = LLMResponse()
        llm_res.token_usage = LLMResponseTokenUsage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            total_tokens=response.usage.total_tokens,
        )
        self.logger.debug(f"llm_res.token_usage:\n {llm_res.token_usage}")
        # 本文を確認する
        for item in response.output:
            if isinstance(item, ResponseOutputMessage):
                # 最終のメッセージを取得する
                for content in item.content:
                    if isinstance(content, ResponseOutputText):
                        llm_res.add_content_text(content.text)
                        if self.config.get("is_output_file", False):
                            # レスポンスをファイルに書き込む
                            self._write_file(content.text)
        return llm_res

    def _parse_response(self, response: ChatCompletion) -> LLMResponse:
        """
        レスポンスを解析するメソッド
        :return: 解析されたレスポンス
        """
        # レスポンスの取得
        self.logger.debug(f"_parse_response response:\n {response}")
        llm_res = LLMResponse()
        llm_res.token_usage = LLMResponseTokenUsage(
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )

        tools = []
        if response.choices[0].message.content:
            llm_res.add_content_text(response.choices[0].message.content)
            if self.config.get("is_output_file", False):
                # レスポンスをファイルに書き込む
                self._write_file(response.choices[0].message.content)

        if response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                tools.append(
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": json.loads(tool_call.function.arguments),
                        },
                    }
                )
            llm_res.add_content_tools(tools)
        return llm_res

    def get_models(self, limit: int = 10):
        models = self.client.models.list()
        model_list = [
            {
                "type": "openai",
                "name": model.id,
                "model": model.id,
            }
            for model in models.data
        ]
        return model_list[:limit]
