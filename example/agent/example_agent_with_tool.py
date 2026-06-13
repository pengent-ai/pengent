import sys
import os
import asyncio

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
)
from pengent.lib import get_logger

logger = get_logger(level=10)
from dotenv import load_dotenv

load_dotenv()

from pengent.agents import AgentBase
from pengent.type.agent import AgentSendOutput
from pengent.core.sessions import Session
from pengent.tools.tool_utils import function_tool
from pengent.llm import (
    LLMOpenAIClient,
    LLMAnthropicClient,
    LLMGeminiClient,
    LLMOpenRouterClient,
)
@function_tool
def get_weather(query: str):
    """
    都市の天気を取得する

    Parameters:
        query (str): 検索する都市名

    """
    return f"{query}の天気は晴れです"

async def example_agent_open_ai_with_tool():
    # LLMクライアントの初期化
    agent = AgentBase(
        name="ExampleAgentOpenAIWithTool",
        llm_client=LLMOpenAIClient(
            model_name="gpt-5-mini",
            temperature=0.3,
        ),
        params={
            "system_prompt": "\n".join(
                [
                    "あなたは天気の窓口案内です。",
                    "`get_weather`を使用して天気情報を提供します。",
                    "引数には都市名を指定してください。(Tokyo, Osakaなど)",
                ]
            ),
        },
        tools=[
            get_weather
        ],
    )
    session = Session(
        session_id="example_session_002",
        user_id="example_user_002",
    )
    output1: AgentSendOutput = await agent.run(
        session, input="東京の天気を教えてください"
    )
    logger.info(f"Agent Output1 : {output1}")
    print(output1.to_dict())

async def example_agent_anthropic_with_tool():
    # LLMクライアントの初期化
    agent = AgentBase(
        name="ExampleAgentAnthropicWithTool",
        llm_client=LLMAnthropicClient(
            model_name="claude-haiku-4-5-20251001",
            temperature=0.3,
        ),
        params={
            "system_prompt": "\n".join(
                [
                    "あなたは天気の窓口案内です。",
                    "`get_weather`を使用して天気情報を提供します。",
                    "引数には都市名を指定してください。(Tokyo, Osakaなど)",
                ]
            ),
        },
        tools=[
            get_weather
        ],
    )
    session = Session(
        session_id="example_session_002",
        user_id="example_user_002",
    )
    output1: AgentSendOutput = await agent.run(
        session, input="東京の天気を教えてください"
    )
    logger.info(f"Agent Output1 : {output1}")
    print(output1.to_dict())

async def example_agent_gemini_with_tool():
    # LLMクライアントの初期化
    agent = AgentBase(
        name="ExampleAgentGeminiWithTool",
        llm_client=LLMGeminiClient(
            model_name="gemini-2.5-flash",
            temperature=0.3,
        ),
        params={
            "system_prompt": "\n".join(
                [
                    "あなたは天気の窓口案内です。",
                    "`get_weather`を使用して天気情報を提供します。",
                    "引数には都市名を指定してください。(Tokyo, Osakaなど)",
                ]
            ),
        },
        tools=[
            get_weather
        ],
    )
    session = Session(
        session_id="example_session_002",
        user_id="example_user_002",
    )
    output1: AgentSendOutput = await agent.run(
        session, input="東京の天気を教えてください"
    )
    logger.info(f"Agent Output1 : {output1}")
    print(output1.to_dict())


async def example_agent_open_router_with_tool():
    # LLMクライアントの初期化
    agent = AgentBase(
        name="ExampleAgentOpenRouterWithTool",
        llm_client=LLMOpenRouterClient(
            temperature=0.3,
        ),
        params={
            "system_prompt": "\n".join(
                [
                    "あなたは天気の窓口案内です。",
                    "`get_weather`を使用して天気情報を提供します。",
                    "引数には都市名を指定してください。(Tokyo, Osakaなど)",
                ]
            ),
        },
        tools=[
            get_weather
        ],
    )
    session = Session(
        session_id="example_session_002",
        user_id="example_user_002",
    )
    output1: AgentSendOutput = await agent.run(
        session, input="東京の天気を教えてください"
    )
    logger.info(f"Agent Output1 : {output1}")
    print(output1.to_dict())



if __name__ == "__main__":
    # asyncio.run(example_agent_open_ai_with_tool())
    # asyncio.run(example_agent_anthropic_with_tool())
    # asyncio.run(example_agent_gemini_with_tool())
    asyncio.run(example_agent_open_router_with_tool())
