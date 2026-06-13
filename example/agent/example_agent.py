import sys
import os
import asyncio

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
)
from dotenv import load_dotenv
load_dotenv()

from pengent.lib import get_logger
logger = get_logger(level=10)

from pengent.agents.basic.agent_chat import AgentChat
from pengent.type.agent.agent_enum import AgentSendOutput
from pengent.core.sessions.session import Session


async def example_agent_run_and_send():
    # LLMクライアントの初期化
    agent = AgentChat()
    session = Session(
        session_id="example_session_001",
        user_id="example_user_001",
    )
    output1: AgentSendOutput = await agent.run(
        session, input="今日は天気がいいですね"
    )
    logger.info(f"Agent Output1 : {output1}")

    output2: AgentSendOutput = await agent.send("こんにちは！", session=session)
    logger.info(f"Agent Output2 : {output2}")

    print(session.events.to_dict())



if __name__ == "__main__":
    asyncio.run(example_agent_run_and_send())
