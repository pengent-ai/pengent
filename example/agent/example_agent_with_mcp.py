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
from pengent.tools.mcp import McpToolPackage

from pengent.llm import (
    LLMOpenAIClient,
    LLMAnthropicClient,
    LLMGeminiClient,
    LLMOpenRouterClient,
)

mcp_tools = McpToolPackage.create_mcp_stdio(
    name="example_stdio_mcp",
    command="python",
    args=["example/tool/mcp/server.py"]
)


async def example_agent_open_ai_with_tool():
    # LLMクライアントの初期化
    agent = AgentBase(
        name="ExampleAgentOpenAIWithMCP",
        llm_client=LLMOpenAIClient(
            model_name="gpt-5-mini",
            temperature=0.3,
        ),
        params={
            "system_prompt": "\n".join(
                [
                    "あなたは挨拶の窓口案内です。",
                    "`hello_world`を使用して挨拶してください。",
                ]
            ),
        },
        tools=[
            mcp_tools
        ],
    )
    session = Session(
        session_id="example_session_003",
        user_id="example_user_003",
    )
    output1: AgentSendOutput = await agent.run(
        session, input="私のお名前は太郎です"
    )
    logger.info(f"Agent Output1 : {output1}")
    print(output1.to_dict())

async def example_agent_anthropic_with_tool():
    # LLMクライアントの初期化
    agent = AgentBase(
        name="ExampleAgentAnthropicWithMCP",
        llm_client=LLMAnthropicClient(
            model_name="claude-haiku-4-5-20251001",
            temperature=0.3,
        ),
        params={
            "system_prompt": "\n".join(
                [
                    "あなたは挨拶の窓口案内です。",
                    "`hello_world`を使用して挨拶してください。",
                ]
            ),
        },
        tools=[
            mcp_tools
        ],
    )
    session = Session(
        session_id="example_session_003",
        user_id="example_user_003",
    )
    output1: AgentSendOutput = await agent.run(
        session, input="私のお名前は太郎です"
    )
    logger.info(f"Agent Output1 : {output1}")
    print(output1.to_dict())

async def example_agent_gemini_with_tool():
    # LLMクライアントの初期化
    agent = AgentBase(
        name="ExampleAgentGeminiWithMCP",
        llm_client=LLMGeminiClient(
            model_name="gemini-2.5-flash",
            temperature=0.3,
        ),
        params={
            "system_prompt": "\n".join(
                [
                    "あなたは挨拶の窓口案内です。",
                    "`hello_world`を使用して挨拶してください。",
                ]
            ),
        },
        tools=[
            mcp_tools
        ],
    )
    session = Session(
        session_id="example_session_003",
        user_id="example_user_003",
    )
    output1: AgentSendOutput = await agent.run(
        session, input="私のお名前は太郎です"
    )
    logger.info(f"Agent Output1 : {output1}")
    print(output1.to_dict())


async def example_agent_open_router_with_tool():
    # LLMクライアントの初期化
    agent = AgentBase(
        name="ExampleAgentOpenRouterWithMCP",
        llm_client=LLMOpenRouterClient(
            temperature=0.3,
        ),
        params={
            "system_prompt": "\n".join(
                [
                    "あなたは挨拶の窓口案内です。",
                    "`hello_world`を使用して挨拶してください。",
                ]
            ),
        },
        tools=[
            mcp_tools
        ],
    )
    session = Session(
        session_id="example_session_003",
        user_id="example_user_003",
    )
    output1: AgentSendOutput = await agent.run(
        session, input="私のお名前は太郎です"
    )
    logger.info(f"Agent Output1 : {output1}")
    print(output1.to_dict())



if __name__ == "__main__":
    # asyncio.run(example_agent_open_ai_with_tool())
    # asyncio.run(example_agent_anthropic_with_tool())
    # asyncio.run(example_agent_gemini_with_tool())
    asyncio.run(example_agent_open_router_with_tool())
