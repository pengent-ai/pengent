import os
import datetime
import tempfile
import shutil
import json
from typing import Dict, Any, Iterator
from openai import OpenAI, NotFoundError
from .llm_batch_base import (
    LLMBatchBase,
    LLMBatchData,
    LLMBatchResponse,
    GetLLMBatchFileData,
    GetLLMBatchSResponse,
    LLMBatchFileData,
    LLMMessage,
    LLMResponse,
    GetLLMBatchOutputDataResponse,
    LLMClientType,
)
from ...type.llm.llm_response import LLMResponseTokenUsage

# from typing import List, Dict, Any,Union
# from dataclasses import dataclass

from ...lib import get_logger

logger = get_logger()


class LLMOpenAIBatchClient(LLMBatchBase):
    """
    LLMバッチ処理用クライアントクラス(Open AI)

    Notes:
        - OpenAIのAPIを使用して、バッチ処理を行うためのクライアントクラスです。
        - 現在はOPENAI以外は対応していない
    """

    API_KEY = os.getenv("OPENAI_API_KEY")

    def __init__(self, model_name="gpt-5-mini", temperature=0.0, config=None):
        super().__init__(
            model_name,
            temperature,
            config,
            llm_type=LLMClientType.OPENAI.value,
        )
        self._type = LLMClientType.OPENAI.value

    @classmethod
    def get_batches(cls, status: str = None) -> GetLLMBatchSResponse:
        client = OpenAI(api_key=cls.API_KEY)
        batches = client.batches.list()
        logger.info(f"get batches list count: {len(batches.data)}")
        results: list[GetLLMBatchFileData] = []
        for batch in batches.data:
            if status and batch.status != status:
                continue

            logger.debug(
                f"ID: {batch.id}, Status: {batch.status}, Created: {batch.created_at}"
            )
            logger.debug(
                f"Endpoint: {batch.endpoint}, Input File ID: {batch.input_file_id}, "
                f"Output File ID: {batch.output_file_id}"
            )
            results.append(
                GetLLMBatchFileData(
                    id=batch.id,
                    status=batch.status,
                    endpoint=batch.endpoint,
                    created_at=datetime.datetime.fromtimestamp(
                        batch.created_at
                    ).isoformat(),
                    completed_at=(
                        datetime.datetime.fromtimestamp(batch.completed_at).isoformat()
                        if batch.completed_at
                        else None
                    ),
                    input_file_id=batch.input_file_id,
                    output_file_id=batch.output_file_id,
                    total_count=batch.request_counts.total,
                    completed_count=batch.request_counts.completed,
                    failed_count=batch.request_counts.failed,
                )
            )

        return GetLLMBatchSResponse(item_count=len(results), items=results)

    @classmethod
    def get_output_file(cls, batch_id: str, output_dir=".batch") -> bool:
        try:
            client = OpenAI(api_key=cls.API_KEY)
            batch_response = client.batches.retrieve(batch_id)
            logger.debug(f"Batch {batch_id} status: {batch_response.status}")
            output_file_id = (
                batch_response.output_file_id
                if batch_response.status == "completed"
                else None
            )
            error_file_id = (
                batch_response.error_file_id
                if batch_response.status == "completed"
                else None
            )

            if not output_file_id and not error_file_id:
                logger.warning(
                    f"Batch {batch_id} is not completed or has no output file."
                )
                return False

            batch_file_dir = os.path.join(output_dir, batch_id)
            if not os.path.exists(batch_file_dir):
                os.makedirs(batch_file_dir, exist_ok=True)

            if output_file_id:
                file_stream = client.files.content(output_file_id)
                output_contents = file_stream.read()
                output_path = os.path.join(
                    batch_file_dir, f"output_{output_file_id}.jsonl"
                )
                with open(output_path, "wb") as f:
                    f.write(output_contents)
                logger.debug(f"Output file saved to: {output_path}")
                file_stream.close()

            if error_file_id:
                file_stream = client.files.content(error_file_id)
                error_contents = file_stream.read()
                error_path = os.path.join(
                    batch_file_dir, f"error_{error_file_id}.jsonl"
                )
                with open(error_path, "wb") as f:
                    f.write(error_contents)
                logger.debug(f"Error file saved to: {error_path}")
                file_stream.close()

            return True
        except NotFoundError as e:
            logger.error(f"Batch {batch_id} not found: {e}")
            return False
        except Exception as e:
            logger.error(f"Error retrieving batch output file: {e}")
            return False

    @classmethod
    def get_output_dict(
        cls, batch_id: str, output_dir=None
    ) -> GetLLMBatchOutputDataResponse:
        try:
            result = []
            client = OpenAI(api_key=cls.API_KEY)
            batch_response = client.batches.retrieve(batch_id)
            logger.debug(f"Batch {batch_id} status: {batch_response.status}")

            if batch_response.status != "completed":
                return None

            output_file_id = (
                batch_response.output_file_id
                if batch_response.status == "completed"
                else None
            )
            error_file_id = (
                batch_response.error_file_id
                if batch_response.status == "completed"
                else None
            )

            if not output_file_id and not error_file_id:
                logger.warning(
                    f"Batch {batch_id} is not completed or has no output file."
                )
                return None

            res = GetLLMBatchOutputDataResponse(
                id=batch_id,
                status=batch_response.status,
                output_file_id=output_file_id if output_file_id else error_file_id,
                created_at=datetime.datetime.fromtimestamp(batch_response.created_at),
                completed_at=datetime.datetime.fromtimestamp(
                    batch_response.completed_at
                )
                if batch_response.completed_at
                else None,
                failed_at=datetime.datetime.fromtimestamp(batch_response.failed_at)
                if batch_response.failed_at
                else None,
                total_count=batch_response.request_counts.total,
                completed_count=batch_response.request_counts.completed,
                failed_count=batch_response.request_counts.failed,
                records=[],
            )

            if output_dir:
                batch_file_dir = os.path.join(output_dir, batch_id)
                if not os.path.exists(batch_file_dir):
                    os.makedirs(batch_file_dir, exist_ok=True)

            if output_file_id:
                logger.debug(f"output file processing: {output_file_id} ")
                file_stream = client.files.content(output_file_id)
                output_contents = file_stream.read()

                if output_dir:
                    output_path = os.path.join(
                        batch_file_dir, f"output_{output_file_id}.jsonl"
                    )
                    with open(output_path, "wb") as f:
                        f.write(output_contents)
                    logger.debug(f"Output file saved to: {output_path}")
                file_stream.close()

                # 各行を辞書に変換(JSON)
                output_str = output_contents.decode("utf-8")
                records = [
                    json.loads(line) for line in output_str.splitlines() if line.strip()
                ]
                result.extend(records)

            if error_file_id:
                file_stream = client.files.content(error_file_id)
                error_contents = file_stream.read()
                if output_dir:
                    error_path = os.path.join(
                        batch_file_dir, f"error_{error_file_id}.jsonl"
                    )
                    with open(error_path, "wb") as f:
                        f.write(error_contents)
                    logger.debug(f"Error file saved to: {error_path}")
                file_stream.close()
                # 各行を辞書に変換(JSOL)
                error_str = error_contents.decode("utf-8")
                error_records = [
                    json.loads(line) for line in error_str.splitlines() if line.strip()
                ]
                result.extend(error_records)
            res.records = result
            return res
        except NotFoundError as e:
            logger.exception(f"Batch {batch_id} not found: {e}")
            return None
        except Exception as e:
            logger.exception(f"Error retrieving batch output file: {e}")
            return None

    @classmethod
    def push(cls, batch_file: LLMBatchFileData):
        logger.debug(
            f"push batch_file: {batch_file.llm_type} {len(batch_file.batch_data)} items"
        )
        # 一時的にJSONLファイルを生成する
        try:
            tmp_dir = tempfile.mkdtemp(prefix="batch_")
            file_path = os.path.join(tmp_dir, f"{batch_file.llm_type}_batch.jsonl")
            logger.debug(f"Temporary file path: {file_path}")

            with open(file_path, "w", encoding="utf-8") as f:
                for record in batch_file.batch_data:
                    f.write(
                        json.dumps(record.format_openai_messages(), ensure_ascii=False)
                        + "\n"
                    )

            client = OpenAI(api_key=cls.API_KEY)
            with open(file_path, "rb") as f:
                upload = client.files.create(file=f, purpose="batch")

            res = client.batches.create(
                input_file_id=upload.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
            )
            batch_file.id = res.id
            batch_file.status = "pushed"
            batch_file.endpoint = res.endpoint
            batch_file.pushed_at = datetime.datetime.fromtimestamp(res.created_at)
            batch_file.input_file_id = res.input_file_id
            batch_file.output_file_id = res.output_file_id
            batch_file.request_count = len(batch_file.batch_data)

            logger.debug(f"batch_file: {batch_file.id}")
            return batch_file
        except Exception as e:
            logger.error(f"Error pushing batch file: {e}")
            return None
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def create_record(
        self, prompt: str = None, messages: LLMMessage = None, **kwargs
    ) -> LLMBatchData:
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

        self.logger.debug(f"message: {msg_temp}")

        # Toolsを設定する
        tools = kwargs.get("tools", self.tools)
        kws = {}

        if tools:
            kws["tools"] = tools
            kws["tool_choice"] = "auto"

        # Web Search TDS
        # is_web_search=kwargs.get("is_web_search",self.is_web_search)

        return LLMBatchData(
            llm_type=self._type,
            messages=msg_temp,
            model_name=self.model_name,
            temperature=self.temperature,
            max_tokens=kwargs.get("max_tokens", self.config.get("max_tokens", None)),
            custom_id=kwargs.get("custom_id", None),
            url="/v1/chat/completions",
            tools=tools,
        )

    @classmethod
    def cancel(cls, batch_id: str) -> bool:
        try:
            client = OpenAI(api_key=cls.API_KEY)
            client.batches.cancel(batch_id)
            logger.info(f"Batch {batch_id} cancelled successfully.")
            return True
        except NotFoundError as e:
            logger.error(f"Batch {batch_id} not found: {e}")
            return False
        except Exception as e:
            logger.error(f"Error cancelling batch {batch_id}: {e}")
            return False

    @classmethod
    def delete(cls, batch_id: str) -> bool:
        """
        バッチ処理を削除するメソッド

        Notes:
            OpenAIのAPIではバッチを削除する機能は提供されていないため、代わりにキャンセルを行う
        """
        return cls.cancel(batch_id)

    @classmethod
    def parse(cls, dic: Dict[str, Any]) -> LLMBatchResponse:
        """レスポンスの辞書からLLMResponse生成するクラスメソッド"""
        response: dict = dic.get("response", None)
        if not response:
            raise ValueError("Response is empty or not found in the dictionary.")

        batch_res = LLMBatchResponse(
            id=dic.get("id", ""),
            custom_id=dic.get("custom_id", ""),
            llm_response=None,
        )

        status_code = response.get("status_code", 200)
        logger.debug(f"parse response status: {status_code}")
        llm_res = LLMResponse()
        if status_code != 200:
            logger.error(
                f"Error in response: {response.get('message', 'Unknown error')}"
            )
            llm_res.add_content_text(
                f"Error: {response.get('message', 'Unknown error')}"
            )
            batch_res.llm_response = llm_res
            return batch_res

        usage: dict = response.get("usage", {})
        llm_res.token_usage = LLMResponseTokenUsage(
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )

        tools = []
        body: dict = response.get("body", {})
        if body.get("choices")[0].get("message", {}).get("content"):
            llm_res.add_content_text(body["choices"][0]["message"]["content"])

        if body.get("choices")[0].get("message", {}).get("tool_calls"):
            for tool_call in body["choices"][0]["message"]["tool_calls"]:
                tools.append(
                    {
                        "id": tool_call["id"],
                        "type": "function",
                        "function": {
                            "name": tool_call["function"]["name"],
                            "arguments": json.loads(tool_call["function"]["arguments"]),
                        },
                    }
                )
            llm_res.add_content_tools(tools)

        batch_res.llm_response = llm_res
        return batch_res

    @classmethod
    def iter_results(cls, batch_file: LLMBatchFileData) -> Iterator[LLMBatchResponse]:
        resulte = cls.get_output_dict(batch_file.id)
        if not resulte:
            return

        logger.debug(
            f"iter_results batch_file: {batch_file.id} result: {len(resulte.records)}"
        )

        batch_file.status = "completed"
        batch_file.completed_at = resulte.completed_at or datetime.datetime.now()
        batch_file.output_file_id = resulte.output_file_id
        batch_file.total_count = resulte.total_count
        batch_file.completed_count = resulte.completed_count
        batch_file.failed_count = resulte.failed_count

        for item in resulte.records:
            res = cls.parse(item)
            if not res:
                logger.warning(f"parse result is None: {item['custom_id']}")
                continue
            yield res
