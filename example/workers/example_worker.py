import sys
import os
from datetime import datetime

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
)
from dotenv import load_dotenv

load_dotenv()

from pengent.lib import get_logger

logger = get_logger(level=10)

from pengent.workers.basic.worker_greet import WorkerGreet
from pengent.workers.basic.worker_call_tool import WorkerCallTool
from pengent.type.agent.agent_enum import AgentSendOutput
from pengent.core.sessions import Session, SessionServiceBase

from pengent.tools.tool_utils import function_tool


@function_tool
def get_weather(query: str):
    """
    都市の天気を取得する

    Parameters:
        query (str): 検索する都市名

    """
    return f"{query}の天気は晴れです"


@function_tool
def get_datetime(query: str):
    """
    都市の天気を取得する

    Parameters:
        query (str): 検索する都市名

    """
    now = datetime.now()
    return f"{query}の日時は{now.strftime('%Y-%m-%d %H:%M:%S')}です"


def example_worker_greet_run_and_send():
    # ワーカーの初期化
    worker = WorkerGreet()
    session = Session(
        session_id="example_worker_session_001",
        user_id="example_user_001",
    )
    output1: AgentSendOutput = worker.run(session, input="こんにちは！")
    logger.info(f"Worker Output: {output1.message}")


def example_worker_call_tool_run_and_send():
    # ワーカーの初期化
    worker = WorkerCallTool(
        tools=[
            get_weather,
            get_datetime,
        ]
    )
    session = Session(
        session_id="example_worker_session_001",
        user_id="example_user_001",
    )

    def run_worker(worker: WorkerCallTool, session: Session, input: str):
        output: AgentSendOutput = worker.run(session, input=input)
        print(output.message)
        logger.info(f"State delta:{output.context.get('state_delta')}")
        if "state_delta" in output.context:
            SessionServiceBase._deep_merge(
                session.state, output.context["state_delta"]
            )

    run_worker(worker, session, "こんにちはツールを使いたいです。")
    input("-- Press Enter to continue --")
    run_worker(worker, session, "queryは東京でお願いします")
    input("-- Press Enter to continue --")
    run_worker(worker, session, "やっぱりqueryは大阪でお願いします")
    input("-- Press Enter to continue --")
    run_worker(worker, session, "はい")

    logger.info("-- Final Session State --")
    logger.info(f"Session:{session.state}")


if __name__ == "__main__":
    # example_worker_greet_run_and_send()
    example_worker_call_tool_run_and_send()
