import sys
import os
import uuid

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
)
from dotenv import load_dotenv
load_dotenv()

from pengent.lib import get_logger
logger = get_logger(level=10)

from pengent.core.sessions.session_service.database_session_service import (
    DatabaseSessionService,
)
from pengent.core.runners import Runner
from pengent.agents import AgentChat
from pengent.llm import LLMGeminiClient

session_id = os.getenv("SAMPLE_SESSION_ID")
user_id = os.getenv("SAMPLE_USER_ID", "example_user_001")

if not session_id:
    session_id = uuid.uuid4().hex

def example_runner_run_and_send():
    session_service = DatabaseSessionService()

    agent = AgentChat(
        llm_client=LLMGeminiClient(
            model_name="gemini-2.5-flash",
            temperature=0.3,
            config={
                "is_output_file": False,
                "max_tokens": 1000,  # 増加: thinking mode 対応
                "system_prompt": "\n".join(
                    [
                        "あなたは優秀な窓口案内です。",
                        "わかりやすく、自然な日本語で丁寧に説明してください。",
                        "誤字や不自然な表現を避け、短めにまとめてください。",
                    ]
                ),
            },
        )
    )
    runner = Runner(
        agent=agent,
        session_service=session_service,
    )
    output = runner.run(
        user_id=user_id,
        session_id=session_id,
        input="こんにちは！",
    )
    logger.info(f"Runner Output: {output.message}")

    output = runner.run(
        user_id=user_id,
        session_id=session_id,
        input="旅行のお話がしたいです。",
    )
    logger.info(f"Runner Output: {output.message}")



if __name__ == "__main__":
    example_runner_run_and_send()
    # example_runner_run_genimi()


