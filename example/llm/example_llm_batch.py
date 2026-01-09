import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
)

from pengent.lib import get_logger

logger = get_logger(level=10)

from dotenv import load_dotenv

# envファイルを読み込む
load_dotenv()

from pengent.llm.batch.llm_batch_base import LLMBatchFileData
from pengent.llm.batch.llm_batch_openai import LLMOpenAIBatchClient
from pengent.llm.batch.llm_batch_anthropic import LLMAnthropicBatchClient
from pengent.agents.basic.agent_coder import AgentCoder


def example_list_openai():
    batches = LLMOpenAIBatchClient.get_batches()
    logger.info(f"Batch List Count: {batches.item_count}")
    logger.info(f"{batches.model_dump_json(indent=2)}")


# example_list_openai()


def example_get_output_file_openai():
    ret = LLMOpenAIBatchClient.get_output_file(
        "batch_68a65eaf65e48190b922cfddd3855aa4"
    )
    logger.info(f"example_get_output_file Response: {ret}")


# example_get_output_file_openai()


def example_read_file_openai():
    ret = LLMOpenAIBatchClient.read_file(
        "batch_68a65eaf65e48190b922cfddd3855aa4"
    )
    logger.info(f"example_read_file Response: {ret}")


# example_read_file_openai()


def example_get_output_dict_openai():
    ret = LLMOpenAIBatchClient.get_output_dict(
        "batch_68a65eaf65e48190b922cfddd3855aa4"
    )
    logger.info(f"example_get_output_dict Response: {ret}")


# example_get_output_dict_openai()


def example_iter_results_openai():
    batch_file = LLMBatchFileData(llm_type="openai")
    batch_file.id = "batch_68a855330e6c8190b6b85a355edcb135"
    for res in LLMOpenAIBatchClient.iter_results(batch_file):
        logger.info(
            f"example_iter_results Response: {res.llm_response.get_message()}"
        )


example_iter_results_openai()


def example_request_without_file_openai():
    batch_client = LLMOpenAIBatchClient()
    res = batch_client.request(
        "LLMのバッチ処理で活用できそうなアイデアをできるだけ多く考えてみてください。",
    )
    logger.info(f"Response: {res.get_message()}")
    logger.info(f"batchfile: {batch_client.batch_file}")


# example_request_without_file_openai()


def example_request_file_openai():
    batch_file = LLMBatchFileData(llm_type="openai")
    batch_client = LLMOpenAIBatchClient()
    batch_client.request(
        "LLMのバッチ処理で活用できそうなアイデアをできるだけ多く考えてみてください。",
        batch_file=batch_file,
    )
    batch_client = LLMOpenAIBatchClient()
    batch_client.request(
        "LLMのバッチ処理でWEB検索を活用することは可能でしょうか？",
        batch_file=batch_file,
    )
    logger.info(f"batchfile: {len(batch_file.batch_data)}")
    res = LLMOpenAIBatchClient.push(batch_file)
    logger.info(f"Response batchfile: {res.id}")


# example_request_file_openai()

# ---------------------------------------------
# claude


def example_list_anthropic():
    batches = LLMAnthropicBatchClient.get_batches()
    logger.info(f"Batch List Count: {batches.item_count}")
    logger.info(f"{batches.model_dump_json(indent=2)}")


# example_list_anthropic()


def example_get_output_file_anthropic():
    ret = LLMAnthropicBatchClient.get_output_file(
        "msgbatch_014KQA6tpaug6xHqX54Cf6PV"
    )
    logger.info(f"example_get_output_file Response: {ret}")


# example_get_output_file_anthropic()


def example_read_file_anthropic():
    ret = LLMAnthropicBatchClient.read_file(
        "msgbatch_014KQA6tpaug6xHqX54Cf6PV"
    )
    logger.info(f"example_read_file Response: {ret}")


# example_read_file_anthropic()


def example_get_output_dict_anthropic():
    ret = LLMAnthropicBatchClient.get_output_dict(
        "msgbatch_014KQA6tpaug6xHqX54Cf6PV"
    )
    logger.info(f"example_get_output_dict Response: {ret}")


# example_get_output_dict_anthropic()


def example_iter_results_anthropic():
    batch_file = LLMBatchFileData(llm_type="anthropic")
    batch_file.id = "msgbatch_014KQA6tpaug6xHqX54Cf6PV"
    for res in LLMAnthropicBatchClient.iter_results(batch_file):
        logger.info(
            f"example_iter_results Response: {res.llm_response.get_message()}"
        )


# example_iter_results_anthropic()


def example_request_without_file_anthropic():
    batch_client = LLMAnthropicBatchClient()
    res = batch_client.request(
        "LLMのバッチ処理で活用できそうなアイデアをできるだけ多く考えてみてください。",
    )
    logger.info(f"Response: {res.get_message()}")
    logger.info(f"batchfile: {batch_client.batch_file}")


# example_request_without_file_anthropic()


def example_request_file_anthropic():
    batch_file = LLMBatchFileData(llm_type="anthropic")
    batch_client = LLMAnthropicBatchClient()
    batch_client.request(
        "LLMのバッチ処理で活用できそうなアイデアをできるだけ多く考えてみてください。",
        batch_file=batch_file,
    )
    batch_client = LLMAnthropicBatchClient()
    batch_client.request(
        "LLMのバッチ処理でWEB検索を活用することは可能でしょうか？",
        batch_file=batch_file,
    )
    logger.info(f"batchfile: {len(batch_file.batch_data)}")
    res = LLMAnthropicBatchClient.push(batch_file)
    logger.info(f"Response batchfile: {res.id}")


# example_request_file_anthropic()


def example_batch_agent_coder():
    # LLMクライアントの初期化
    batch_client = LLMOpenAIBatchClient()
    agent = AgentCoder(llm_client=batch_client)
    agent.run()
    output = agent.send(
        "Dockerfileの書き方、特にオプションやコマンドの使い方について教えてください。"
    )
    logger.info(f"Output: {output.message}")


# example_batch_agent_coder()
