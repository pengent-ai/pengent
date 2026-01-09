import uuid
import datetime
import os
import json
from queue import Queue

from typing import Dict, Any, List, Iterator
from pydantic import BaseModel, Field
from typing import Optional
from ..llm_client_base import LLMClientBase, LLMMessage, LLMResponse
from ...type.llm.llm_message import LLMClientType


class GetLLMBatchFileData(BaseModel):
    """バッチデータモデル"""

    id: str = Field(..., description="バッチID")
    status: str = Field(..., description="バッチのステータス")
    endpoint: Optional[str] = Field(None, description="バッチのエンドポイントURL")
    created_at: str = Field(..., description="バッチの作成日時")
    completed_at: Optional[str] = Field(None, description="バッチの完了日時")
    input_file_id: Optional[str] = Field(None, description="入力ファイルのID")
    output_file_id: Optional[str] = Field(None, description="出力ファイルのID")
    total_count: int = Field(..., description="バッチの総数")
    completed_count: int = Field(..., description="完了したバッチの数")
    failed_count: int = Field(..., description="失敗したバッチの数")


class GetLLMBatchSResponse(BaseModel):
    """バッチ一覧取得レスポンスモデル"""

    items: list[GetLLMBatchFileData] = Field(..., description="バッチデータのリスト")
    item_count: int = Field(..., description="バッチデータの総数")


class GetLLMBatchOutputDataResponse(BaseModel):
    """バッチ出力データレスポンスモデル"""

    id: str = Field(..., description="バッチID")
    status: str = Field(..., description="バッチのステータス")
    output_file_id: Optional[str] = Field(None, description="出力ファイルのID")
    created_at: datetime.datetime = Field(..., description="バッチの作成日時")
    completed_at: Optional[datetime.datetime] = Field(
        None, description="バッチの完了日時"
    )
    failed_at: Optional[datetime.datetime] = Field(None, description="バッチの失敗日時")
    total_count: int = Field(..., description="バッチの総数")
    completed_count: int = Field(..., description="完了したバッチの数")
    failed_count: int = Field(..., description="失敗したバッチの数")
    records: List[Dict[str, Any]] = Field(..., description="バッチのレコードリスト")


class LLMBatchResponse:
    """
    バッチレスポンスモデル
    """
    def __init__(
        self,
        id: str,
        custom_id: str,
        llm_response: LLMResponse,
    ):
        self.id = id
        self.custom_id = custom_id
        self.llm_response = llm_response


class LLMBatchData:
    """
    バッチ処理用のデータクラス
    """

    def __init__(
        self,
        llm_type: LLMClientType,
        messages: List[dict],
        model_name: str,
        temperature: float = None,
        max_tokens: Optional[int] = None,
        custom_id: Optional[str] = None,
        url: Optional[str] = None,
        tools: Optional[List[dict]] = None,
    ):
        self.llm_type = llm_type
        self.messages = messages
        self.model_name = model_name
        self.custom_id = custom_id if custom_id else str(uuid.uuid4())
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.url = url if url else "/v1/chat/completions"
        self.tools = tools

    def format_openai_messages(self):
        """
        OpenAIのメッセージ形式に変換するメソッド
        :return: OpenAI形式のメッセージリスト
        """
        ret = {
            "custom_id": self.custom_id,
            "method": "POST",
            "url": self.url,
            "body": {
                "model": self.model_name,
                "messages": self.messages,
            },
        }
        if (
            self.model_name not in ["gpt-5-mini", "gpt-5"]
            and self.temperature is not None
        ):
            ret["body"]["temperature"] = self.temperature

        if (
            self.model_name not in ["gpt-5-mini", "gpt-5"]
            and self.max_tokens is not None
        ):
            ret["body"]["max_tokens"] = self.max_tokens

        return ret

    def format_anthropic_messages(self):
        """
        Anthropicのメッセージ形式に変換するメソッド
        :return: Anthropic形式のメッセージリスト
        """
        ret = {
            "custom_id": self.custom_id,
            "params": {
                "model": self.model_name,
                "messages": self.messages,
            },
        }
        if self.temperature is not None:
            ret["params"]["temperature"] = self.temperature

        if self.max_tokens is not None:
            ret["params"]["max_tokens"] = self.max_tokens

        return ret


class LLMBatchFileData:
    """
    バッチ処理用のデータクラス
    """

    def __init__(self, llm_type: str, storage=None):
        self.llm_type = llm_type
        self.batch_data: List[LLMBatchData] = []
        self.id = None
        self.status = "created"
        self.endpoint = None
        self.created_at = datetime.datetime.now()
        self.pushed_at = None
        self.completed_at = None
        self.input_file_id = None
        self.output_file_id = None
        self.request_count = 0
        self.total_count = 0
        self.completed_count = 0
        self.failed_count = 0
        self.storage = storage

    def add(self, batch_data: LLMBatchData):
        """
        バッチデータを追加するメソッド
        :param batch_data: LLMBatchDataインスタンス
        """
        if not isinstance(batch_data, LLMBatchData):
            raise TypeError("batch_data must be an instance of LLMBatchData")
        self.batch_data.append(batch_data)


class LLMBatchBase(LLMClientBase):
    """
    LLMバッチ処理用クライアントベースクラス
    """

    def __init__(
        self,
        model_name,
        temperature=0.0,
        config=None,
        llm_type="",
        batch_file: LLMBatchFileData = None,
    ):
        super().__init__(model_name, temperature, config, llm_type)
        self._file: LLMBatchFileData = batch_file

    @property
    def batch_file(self) -> Optional[LLMBatchFileData]:
        return self._file

    @batch_file.setter
    def batch_file(self, value: LLMBatchFileData):
        if not isinstance(value, LLMBatchFileData):
            raise TypeError("batch_file must be an instance of LLMBatchFileData")
        self._file = value

    def create_record(
        self, prompt: str = None, messages: LLMMessage = None, **kwargs
    ) -> LLMBatchData:
        """
        バッチリクエストを生成するメソッド
        """
        raise NotImplementedError("This method should be implemented in subclasses")

    def request(
        self,
        prompt: str = None,
        messages: LLMMessage = None,
        batch_file: LLMBatchFileData = None,
        batch_queue: Queue[LLMBatchData] = None,
        **kwargs,
    ) -> LLMResponse:
        batch_data = self.create_record(prompt=prompt, messages=messages, **kwargs)

        batch_file = batch_file if batch_file else self.batch_file
        if batch_file:
            self.logger.debug(f"batch_file added: {batch_data.custom_id}")
            batch_file.add(batch_data)
            res = LLMResponse()
            res.add_content_text(
                f"Batch data({batch_data.custom_id}) added to batch file."
            )
            return res
        elif batch_queue:
            self.logger.debug(f"batch_queue added: {batch_data.custom_id}")
            batch_queue.put(batch_data)
            res = LLMResponse()
            res.add_content_text(
                f"Batch data({batch_data.custom_id}) added to batch queue."
            )
            return res
        else:
            self.logger.debug(f"batch_file create and push: {batch_data.custom_id}")
            # バッチファイルが指定されていない場合は、
            # ファイルを生成して直接リクエストを送信する
            file = LLMBatchFileData(llm_type=self._type)
            file.add(batch_data)
            self.batch_file = file
            push_res = self.push(file)
            res = LLMResponse()
            res.add_content_text(
                f"Created BatchFile and Push.\nBatch File ID: {push_res.id}\n"
                 "Batch data(custom_id={batch_data.custom_id})."
            )
            return res

    @classmethod
    def push(cls, batch_file: LLMBatchFileData):
        """
        バッチファイルをサーバーに送信するクラスメソッド
        """

    @classmethod
    def get_batches(cls, status: str = None) -> GetLLMBatchSResponse:
        """
        バッチの一覧を取得するクラスメソッド
        """

    @classmethod
    def iter_results(cls, batch_file: LLMBatchFileData) -> Iterator[LLMBatchResponse]:
        """
        バッチファイルの結果をイテレータで取得するクラスメソッド
        """

    @classmethod
    def get_output_dict(
        cls, batch_id: str, output_dir=None
    ) -> GetLLMBatchOutputDataResponse:
        """
        バッチファイルの出力ファイルコンテンツを取得するクラスメソッド
        """
        raise NotImplementedError("This method should be implemented in subclasses")

    @classmethod
    def get_output_file(cls, batch_id: str, output_dir=".batch") -> bool:
        """
        バッチファイルの出力ファイルを取得するクラスメソッド
        """
        raise NotImplementedError("This method should be implemented in subclasses")

    @classmethod
    def read_file(
        cls, batch_id: str, output_dir: str = ".batch"
    ) -> List[Dict[str, Any]]:
        """
        指定された batch_id のディレクトリ配下にある JSONL ファイルを読み込み、
        各行を JSON としてパースしたリストを返す。

        Args:
            batch_id (str): バッチID
            output_dir (str): 出力ディレクトリ (デフォルト: ".batch")

        Returns:
            List[Dict[str, Any]]: JSONLの各行を辞書化したリスト
        """
        batch_dir = f"{output_dir}/{batch_id}"
        results: List[Dict[str, Any]] = []

        if not os.path.exists(batch_dir):
            raise FileNotFoundError(f"Batch directory not found: {batch_dir}")

        # ディレクトリ内の .jsonl ファイルを探す
        for fname in os.listdir(batch_dir):
            if not fname.endswith(".jsonl"):
                continue
            file_path = os.path.join(batch_dir, fname)

            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        results.append(obj)
                    except json.JSONDecodeError as e:
                        raise ValueError(
                            f"Failed to parse JSON from line: {line}\nError: {e}"
                        ) from e

        return results

    @classmethod
    def cancel(cls, batch_id: str) -> bool:
        """
        バッチ処理をキャンセルするメソッド
        """
        raise NotImplementedError("This method should be implemented in subclasses")

    @classmethod
    def delete(cls, batch_id: str) -> bool:
        """
        バッチ処理を削除するメソッド
        """
        raise NotImplementedError("This method should be implemented in subclasses")
