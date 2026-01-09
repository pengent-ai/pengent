import os
import importlib.util
from .llm_client_base import LLMClientBase, LLMResponse, LLMMessage
from ..type.llm.llm_message import LLMClientType
from ..type.llm.llm_response import LLMResponseTokenUsage


class LLMGGUFClient(LLMClientBase):
    """
    GGUFClient LLMクライアントクラス
    """

    def __init__(self, model_name="", temperature=0.0, config: dict = None):
        """
        コンストラクタ

        Args:
            model_name (str): モデルファイルのパス
            temperature (float): 温度パラメータ
            config (dict): その他の設定
        Notes:
            - 利用するには、llama-cpp-pythonパッケージが必要です。
        """
        super().__init__(
            model_name, temperature, config, llm_type=LLMClientType.GGUF.value
        )
        if config and config.get("is_auto_setup", True):
            self.setup()

    def setup(self):
        """
        llama-cpp-pythonの初期化メソッド
        """
        # 1回の推論で扱える 最大トークン数(入力 + 出力を含む)
        # メモリ使用量が増える(VRAMやRAM)
        n_ctx = self.config.get("n_ctx", 512)
        # スレッド数(CPUコア数)
        # 値を大きくすると高速化されるが、CPU使用率と発熱が増える
        n_threads = self.config.get("n_threads", 2)
        n_batch = self.config.get("n_batch", 32)

        # model_nameのファイルが存在しない場合はエラーを返す
        if not self.model_name:
            raise ValueError("No set model_name.")
        if not os.path.exists(self.model_name):
            raise FileNotFoundError(f"Not found model_file: : {self.model_name}")

        if importlib.util.find_spec("llama_cpp") is None:
            raise ImportError(
                "llama-cpp-python package is required for LLMGGUFClient. "
                "Please install it via 'pip install llama-cpp-python'."
            )
        from llama_cpp import Llama
        self.llm = Llama(  # noqa: F821
            model_path=self.model_name,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_batch=n_batch,
        )

    def request(self, prompt=None, messages: list = None, **kwargs):
        """
        Qwen/llama-cpp向けにリクエストを送信するメソッド
        :param prompt: 単一プロンプト文字列
        :param messages: Chat形式メッセージリスト(role: user/assistant/system)
        :param kwargs: その他(system_promptなど)
        :return: モデルの応答
        """
        if messages:
            msg_temp = LLMMessage.to_format_messages(messages)
        elif prompt:
            msg_temp = [{"role": "user", "content": prompt.strip()}]
        else:
            raise ValueError("not set prompt.")

        system_prompt = kwargs.get("system_prompt") or self.config.get(
            "system_prompt", ""
        )
        if system_prompt:
            msg_temp.insert(0, {"role": "system", "content": system_prompt})

        # Qwen形式に変換
        full_prompt = self._format_qwen_prompt(messages)

        # llama-cpp-python 実行
        result = self.llm(
            prompt=full_prompt,
            max_tokens=self.config.get("max_tokens", 1000),
            stop=self.config.get("stop", None),
            echo=False,
        )
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
        if result["choices"][0].get("text"):
            tools_dict = self.parse_tools(result["choices"][0]["text"].strip())
            if not tools_dict:
                llm_res.add_content_text(result["choices"][0]["text"].strip())
                if self.config.get("is_output_file", False):
                    # レスポンスをファイルに書き込む
                    self._write_file(result["choices"][0]["text"].strip())
            else:
                # ツールの結果をメッセージに追加
                for tool in tools_dict:
                    tools.append(
                        {
                            "id": "-1",
                            "type": "function",
                            "function": {
                                "name": tool["name"],
                                "arguments": tool["parameters"],
                            },
                        }
                    )
                llm_res.add_content_prompt_tools(tools)

        return llm_res

    def _format_qwen_prompt(self, messages: list[dict]) -> str:
        parts = []
        for m in messages:
            role = m["role"]
            content = m["content"].strip()
            parts.append(f"<|im_start|>{role}\n{content}\n<|im_end|>")
        parts.append("<|im_start|>assistant\n")  # モデルが続きを生成
        return "\n".join(parts)
