import os
import datetime
import json
import requests
from typing import Dict, Any, List, Iterator

from .llm_batch_base import (
    LLMBatchBase,
    LLMClientType,
    LLMBatchData,
    LLMBatchResponse,
    GetLLMBatchFileData,
    GetLLMBatchSResponse,
    LLMBatchFileData,
    LLMMessage,
    LLMResponse,
    GetLLMBatchOutputDataResponse,
)
from ...type.llm.llm_response import LLMResponseTokenUsage

from ...lib import get_logger

logger = get_logger()


class LLMAnthropicBatchClient(LLMBatchBase):
    """
    LLMバッチ処理用クライアントクラス(Anthropic)

    Notes:
        - AnthropicのAPIを使用して、バッチ処理を行うためのクライアントクラスです。
        - 現在はAnthropic以外は対応していない
    """

    API_KEY = os.getenv("CLAUDE_AI_API_KEY")
    VERSION = os.getenv("CLAUDE_AI_VERSION", "2023-06-01")

    def __init__(
        self, model_name="claude-3-5-haiku-20241022", temperature=0.0, config=None
    ):
        super().__init__(
            model_name, temperature, config, llm_type=LLMClientType.ANTHROPIC.value
        )
        self._type = LLMClientType.ANTHROPIC.value

    @classmethod
    def get_batches(cls, status: str = None) -> GetLLMBatchSResponse:
        headers = {
            "x-api-key": cls.API_KEY,
            "anthropic-version": cls.VERSION,
        }
        response = requests.get(
            "https://api.anthropic.com/v1/messages/batches", headers=headers
        )
        response.raise_for_status()
        batches = response.json()
        logger.debug(f"get batches list: {batches}")

        results: list[GetLLMBatchFileData] = []
        for batch in batches["data"]:
            results.append(
                GetLLMBatchFileData(
                    id=batch["id"],
                    status=batch["processing_status"],
                    endpoint=None,
                    created_at=batch["created_at"],
                    completed_at=(batch["ended_at"] if batch.get("ended_at") else None),
                    input_file_id=None,
                    output_file_id=batch.get("results_url"),
                    total_count=batch.get("request_counts", {}).get("total", 0),
                    completed_count=batch.get("request_counts", {}).get("succeeded", 0),
                    failed_count=batch.get("request_counts", {}).get("errored", 0),
                )
            )
        return GetLLMBatchSResponse(item_count=len(results), items=results)

    @classmethod
    def get_output_file(cls, batch_id: str, output_dir=".batch") -> bool:
        try:
            headers = {
                "x-api-key": cls.API_KEY,
                "anthropic-version": cls.VERSION,
            }
            batch_url = f"https://api.anthropic.com/v1/messages/batches/{batch_id}"
            meta_res = requests.get(batch_url, headers=headers)
            meta_res.raise_for_status()
            batch_meta = meta_res.json()
            logger.debug(f"api send url: {batch_url} status: {meta_res.status_code}")
            # 例: {"id": "...", "status": "ended", "results_url": "...", ...}
            status = batch_meta.get("processing_status") or batch_meta.get("status")

            if status != "ended":
                logger.warning(f"Batch {batch_id} is not completed yet.")
                return False

            results_url = batch_meta.get("results_url")
            if not results_url:
                logger.warning(f"Batch {batch_id} has no results URL.")
                return False

            results_res = requests.get(results_url, headers=headers, stream=True)
            results_res.raise_for_status()
            logger.debug(
                f"api send url: {results_url} status: {results_res.status_code}"
            )

            batch_file_dir = os.path.join(output_dir, batch_id)
            if not os.path.exists(batch_file_dir):
                os.makedirs(batch_file_dir, exist_ok=True)

            ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
            output_path = os.path.join(batch_file_dir, f"anth_{ts}.jsonl")

            # write stream to file
            with open(output_path, "wb") as f:
                for chunk in results_res.iter_content(chunk_size=1024 * 64):
                    if chunk:  # keep-alive の空チャンク避け
                        f.write(chunk)

            logger.info(f"Batch output saved to: {output_path}")
            return True

        except requests.RequestException as e:
            logger.error(f"Request error while retrieving batch output file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error retrieving batch output file: {e}")
            return False

    @classmethod
    def get_output_dict(
        cls, batch_id: str, output_dir=None
    ) -> GetLLMBatchOutputDataResponse:
        try:
            headers = {
                "x-api-key": cls.API_KEY,
                "anthropic-version": cls.VERSION,
            }
            batch_url = f"https://api.anthropic.com/v1/messages/batches/{batch_id}"
            meta_res = requests.get(batch_url, headers=headers)
            meta_res.raise_for_status()
            batch_meta: dict = meta_res.json()
            logger.debug(f"api send url: {batch_url} status: {meta_res.status_code}")
            # 例: {"id": "...", "status": "ended", "results_url": "...", ...}
            status = batch_meta.get("processing_status") or batch_meta.get("status")

            if status != "ended":
                return None

            results_url = batch_meta.get("results_url")
            if not results_url:
                logger.warning(f"Batch {batch_id} has no results URL.")
                return None

            # logger.debug(f"batch_meta: {batch_meta}")
            request_counts: dict = batch_meta.get("request_counts", {})
            total_count = request_counts.get("processing", 0)
            total_count += request_counts.get("succeeded", 0)
            total_count += request_counts.get("errored", 0)
            total_count += request_counts.get("canceled", 0)
            total_count += request_counts.get("expired", 0)

            res = GetLLMBatchOutputDataResponse(
                id=batch_id,
                status=status,
                output_file_id=results_url,
                created_at=batch_meta.get("created_at"),
                completed_at=batch_meta.get("ended_at")
                if batch_meta.get("completed_count")
                else None,
                failed_at=batch_meta.get("ended_at")
                if batch_meta.get("failed_count")
                else None,
                total_count=total_count,
                completed_count=request_counts.get("succeeded"),
                failed_count=request_counts.get("errored"),
                records=[],
            )

            if output_dir:
                batch_file_dir = os.path.join(output_dir, batch_id)
                if not os.path.exists(batch_file_dir):
                    os.makedirs(batch_file_dir, exist_ok=True)

            results_res = requests.get(results_url, headers=headers, stream=True)
            results_res.raise_for_status()
            logger.debug(
                f"api send url: {results_url} status: {results_res.status_code}"
            )

            output_data = []
            for line in results_res.iter_lines():
                if line:
                    output_data.append(json.loads(line))

            if output_dir:
                ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
                output_path = os.path.join(batch_file_dir, f"anth_{ts}.jsonl")
                with open(output_path, "wb") as f:
                    for item in output_data:
                        f.write(json.dumps(item).encode("utf-8") + b"\n")

            res.records = output_data
            return res

        except requests.RequestException as e:
            logger.error(f"Request error while retrieving batch output dict: {e}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving batch output dict: {e}")
            return None

    @classmethod
    def push(cls, batch_file: LLMBatchFileData):
        logger.debug(
            f"push batch_file: {batch_file.llm_type} {len(batch_file.batch_data)} items"
        )
        try:
            headers = {
                "x-api-key": cls.API_KEY,
                "anthropic-version": cls.VERSION,
                "content-type": "application/json",
            }
            url = "https://api.anthropic.com/v1/messages/batches"

            payload = {
                "requests": [
                    record.format_anthropic_messages()
                    for record in batch_file.batch_data
                ]
            }

            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            logger.debug(f"Response data: {response_data}")

            batch_file.id = response_data["id"]
            batch_file.status = "pushed"
            batch_file.endpoint = url
            batch_file.pushed_at = datetime.datetime.fromisoformat(
                response_data["created_at"]
            )
            batch_file.output_file_id = response_data.get("results_url")
            batch_file.request_count = response_data.get(
                "request_counts", len(batch_file.batch_data)
            )

            logger.info(f"Successfully pushed batch file: {batch_file.llm_type}")
            return batch_file
        except Exception as e:
            logger.exception(f"Error pushing batch file: {e}")
            return None

    def create_record(
        self, prompt: str = None, messages: LLMMessage = None, **kwargs
    ) -> LLMBatchData:
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
        tools = kwargs.get("tools", self.tools)
        if tools:
            kws["tools"] = tools
            kws["tool_choice"] = "auto"

        if self.config.get("max_tokens", None):
            kws["max_tokens"] = self.config

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

        return LLMBatchData(
            llm_type=self._type,
            messages=msg_temp,
            model_name=self.model_name,
            temperature=self.temperature,
            max_tokens=self.config.get("max_tokens", 2048),
            custom_id=kwargs.get("custom_id", None),
            url="/v1/messages/batches",
            tools=tools,
        )

    @classmethod
    def cancel(cls, batch_id: str) -> bool:
        try:
            headers = {
                "x-api-key": cls.API_KEY,
                "anthropic-version": cls.VERSION,
            }
            url = f"https://api.anthropic.com/v1/messages/batches/{batch_id}/cancel"
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            logger.info(f"Batch {batch_id} cancelled successfully.")
            return True
        except requests.RequestException as e:
            logger.error(f"Request error while cancelling batch {batch_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error cancelling batch {batch_id}: {e}")
            return False

    @classmethod
    def delete(cls, batch_id: str) -> bool:
        try:
            headers = {
                "x-api-key": cls.API_KEY,
                "anthropic-version": cls.VERSION,
            }
            url = f"https://api.anthropic.com/v1/messages/batches/{batch_id}"
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            logger.info(f"Batch {batch_id} deleted successfully.")
            return True
        except requests.RequestException as e:
            logger.error(f"Request error while deleting batch {batch_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting batch {batch_id}: {e}")
            return False

    @classmethod
    def parse(cls, dic: Dict[str, Any]) -> LLMBatchResponse:
        """レスポンスの辞書からLLMResponse生成するクラスメソッド"""
        result: dict = dic.get("result", None)
        if not result:
            raise ValueError("Response is empty or not found in the dictionary.")

        batch_res = LLMBatchResponse(
            id=dic.get("custom_id", ""),
            custom_id=dic.get("custom_id", ""),
            llm_response=None,
        )

        status = result.get("type")  # "succeeded"
        message: dict = result.get("message", {})
        logger.debug(f"parse response status: {status}")
        llm_res = LLMResponse()

        if status != "succeeded":
            logger.error(f"Error in response: status={status}, message={message}")
            llm_res.add_content_text(
                f"Error in response: status={status}, message={message}"
            )
            batch_res.llm_response = llm_res
            return batch_res

        usage: dict = message.get("usage", {})
        llm_res.token_usage = LLMResponseTokenUsage(
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
        )

        texts = []
        tools = []
        contents: List[dict] = message.get("content", [])
        for item in contents:
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

        if tools:
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
