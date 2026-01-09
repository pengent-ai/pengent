import sys
import os
import asyncio
import json

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
)

from pengent.lib import get_logger

logger = get_logger(level=10)

from dotenv import load_dotenv

load_dotenv()

from pengent.tools.tool_utils import function_tool
from pengent.llm.stream.llm_client_stream_openai import LLMOpenAIClientStream
from pengent.llm.stream.llm_client_stream_anthropic import LLMAnthropicClientStream
from pengent.llm.stream.llm_client_stream_gemini import LLMGeminiClientStream
from pengent.type.llm.llm_message import LLMMessage
from pengent.type.llm.llm_response import (
    ResponseText,
    ResponseTools,
)


@function_tool
def get_weather(query: str):
    """
    都市の天気を取得する

    Parameters:
        query (str): 検索する都市名

    """
    return f"{query}の天気=晴れ,気温=25度"


@function_tool
def get_time(query: str):
    """
    都市の時間を取得する

    Parameters:
        query (str): 検索する都市名

    """
    return f"{query}の時間は12:00です"

tool_map = {
    get_weather.name: get_weather,
    get_time.name: get_time,
}

async def example_request_stream_openai():
    llm_client = LLMOpenAIClientStream(
        model_name="gpt-4o-mini",
        temperature=0.2,
        config={"is_output_file": False},
    )
    prompt = "富士山はどこにある？"

    async for event in llm_client.request(prompt=prompt):
        print("----", event)
        if isinstance(event, ResponseText):
            print(f"Text Event OK: {event.text}")

async def example_request_stream_anthropic():
    llm_client = LLMAnthropicClientStream(
        temperature=0.2,
        config={"is_output_file": False},
    )
    prompt = "富士山はどこにある？"

    async for event in llm_client.request(prompt=prompt):
        if isinstance(event, ResponseText):
            print(f"Text Event OK: {event.text}")


async def example_request_stream_gemini():
    llm_client = LLMGeminiClientStream(
        temperature=0.2,
        config={"is_output_file": False},
    )
    prompt = "富士山はどこにある？"

    async for event in llm_client.request(prompt=prompt):
        if isinstance(event, ResponseText):
            print(f"Text Event OK: {event.text}")




async def example_request_stream_openai_with_tools():
    llm_messages = [
        LLMMessage.create_user_message(
            content="今の東京の天気を教えてください。",
        )
    ]
    llm_client = LLMOpenAIClientStream(
        model_name="gpt-4o-mini",
        temperature=0.2,
        config={"is_output_file": False},
    )
    llm_client.tools = [
        get_weather.dump(),
        get_time.dump(),
    ]

    tool_map = {
        get_weather.name: get_weather,
        # get_time.name: get_time,
    }

    async for event in llm_client.request(messages=llm_messages):
        # print("----",event)
        if isinstance(event, ResponseText):
            print(f"Text Event OK: {event.text}")
            llm_messages.append(
                LLMMessage.create_assistant_message(
                    content=event.text,
                )
            )
        elif isinstance(event, ResponseTools):
            print(f"Tool Call Event OK: {event.tools}")
            llm_messages.append(
                LLMMessage.create_meta_data(
                    "openai_stream_meta",
                    {
                        "type": event.tools[0].meta_data.get("type"),
                        "id": event.tools[0].meta_data.get("func_id"),
                        "name": event.tools[0].function.name,
                        "call_id": event.tools[0].id,
                        "arguments": json.dumps(
                            event.tools[0].function.arguments
                        ),
                        "status": "completed",
                    },
                )
            )
            # Call the tool functions Exec
            _tool = tool_map[event.tools[0].function.name]
            result = _tool.run(**event.tools[0].function.arguments)
            if isinstance(result, list) or isinstance(result, dict):
                result = json.dumps(result)
            print(f"Tool Exec Result: {result}")
            llm_messages.append(
                LLMMessage.create_meta_data(
                    "openai_stream_meta",
                    {
                        "type": "function_call_output",
                        "call_id": event.tools[0].id,
                        "output": json.dumps({
                        event.tools[0].function.name: result
                        })
                    },
                )
            )
    
    async for event2 in llm_client.request(messages=llm_messages):
        if isinstance(event2, ResponseText):
            print(f"Final Text: {event2.text}")

async def example_request_stream_anthropic_with_tools():
    llm_messages = [
        LLMMessage.create_user_message(
            content="今の東京の天気を教えてください。",
        )
    ]
    llm_client = LLMAnthropicClientStream(
        temperature=0.2,
        config={"is_output_file": False},
    )
    llm_client.tools = [
        get_weather.dump(),
        get_time.dump(),
    ]

    async for event in llm_client.request(messages=llm_messages):
        # print("----",event)
        if isinstance(event, ResponseText):
            llm_messages.append(
                LLMMessage.create_assistant_message(
                    content=event.text,
                )
            )
        if isinstance(event, ResponseTools):
            llm_messages.append(
                LLMMessage.create_tools_call(
                    tools=event.tools,
                )
            )
            # Call the tool functions Exec
            _tool = tool_map[event.tools[0].function.name]
            result = _tool.run(**event.tools[0].function.arguments)
            if isinstance(result, list) or isinstance(result, dict):
                result = json.dumps(result)
            llm_messages.append(
                LLMMessage.create_tools_result(
                    tool_call_id=event.tools[0].id,
                    content=result
                )
            )

    async for event2 in llm_client.request(messages=llm_messages):
        if isinstance(event2, ResponseText):
            print(f"Final Text: {event2.text}")

async def example_request_stream_gemini_with_tools():
    llm_messages = [
        LLMMessage.create_user_message(
            content="今の東京の天気を教えてください。",
        )
    ]
    llm_client = LLMGeminiClientStream(
        temperature=0.2,
        config={"is_output_file": False},
    )
    llm_client.tools = [
        get_weather.dump(),
        get_time.dump(),
    ]

    async for event in llm_client.request(messages=llm_messages):
        # print("----",event)
        if isinstance(event, ResponseText):
            llm_messages.append(
                LLMMessage.create_assistant_message(
                    content=event.text,
                )
            )
        if isinstance(event, ResponseTools):
            llm_messages.append(
                LLMMessage.create_tools_call(
                    tools=event.tools,
                )
            )
            # Call the tool functions Exec
            _tool = tool_map[event.tools[0].function.name]
            result = _tool.run(**event.tools[0].function.arguments)
            print(f"Tool Exec Result: {result}")
            if isinstance(result, list) or isinstance(result, dict):
                result = json.dumps(result,ensure_ascii=False)
            llm_messages.append(
                LLMMessage.create_tools_result(
                    tool_call_id=event.tools[0].id,
                    content=result
                )
            )

    async for event2 in llm_client.request(messages=llm_messages):
        if isinstance(event2, ResponseText):
            print(f"Final Text: {event2.text}")




if __name__ == "__main__":
    # asyncio.run(example_request_stream_openai())
    # asyncio.run(example_request_stream_anthropic())
    # asyncio.run(example_request_stream_gemini())
    # asyncio.run(example_request_stream_openai_with_tools())
    # asyncio.run(example_request_stream_anthropic_with_tools())
    asyncio.run(example_request_stream_gemini_with_tools())
