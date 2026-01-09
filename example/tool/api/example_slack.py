import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
)

from pengent.lib import get_logger

logger = get_logger(level=10)

from dotenv import load_dotenv

load_dotenv()

from pengent.tools.api.chat.api_slack import ApiSlack


def example():
    api = ApiSlack()
    # res = api.get_channels()
    # logger.debug(res)
    channel_id = "XXXXXXXXXXX"

    channel_id = "C08UU2G7P9R"
    message = "Hello, Slack!"
    res = api.send_message(channel_id=channel_id, message=message)
    logger.debug(res)


example()

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
