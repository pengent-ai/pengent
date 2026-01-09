import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
)

from pengent.lib import get_logger

logger = get_logger(level=10)

from dotenv import load_dotenv

load_dotenv()

from pengent.tools.api.chat.api_rocket_chat import ApiRocketChat


def example_user():
    api = ApiRocketChat()
    res = api.get_users()
    logger.debug(res)

    # 追加する処理
    # res = api.create_user(
    #     username="XXXXXX",
    #     name="XXXX",
    #     email="XXXXX",
    #     password="XXXXX",
    #     roles=["user"],
    #     verified=True,
    #     require_password_change=True
    # )
    # logger.debug(res)

    # 削除する処理
    # res = api.show_user(user_name="wada.y")
    # logger.debug(res)
    # if res.get("_id"):
    #     res = api.delete_user(user_id=res["_id"])
    #     logger.debug(res)


def example_channel():
    api = ApiRocketChat()
    api.get_channels()
    api.get_groups()


# example_user()
example_channel()
