import requests
import os
from ....lib.custom_logger import get_logger


logger = get_logger()


class ApiSlack:
    """
    Slack APIを操作するクラス

    Notes:
        - https://api.slack.com/appsよりAPPを作成する


    """

    SLACK_OAUTH_TOKEN = os.getenv(
        "SLACK_BOT_USER_OAUTH_TOKEN"
    )  # RocketChatのAPIエンドポイント

    @classmethod
    def get_headers(cls):
        """
        APIリクエスト用のヘッダーを取得する
        """
        return {
            "Authorization": f"Bearer {cls.SLACK_OAUTH_TOKEN}",
            "Content-Type": "application/json",
        }

    @classmethod
    def get_channels(cls, limit=100):
        """
        Slackのチャンネル一覧を取得する

        Args:
            limit (int): 取得するチャンネル数の上限

        Returns:
            list: チャンネル情報のリスト
        """
        url = "https://slack.com/api/conversations.list"
        params = {"limit": limit, "types": "public_channel,private_channel"}
        response = requests.get(url, headers=cls.get_headers(), params=params)
        response.raise_for_status()
        json_data = response.json()
        logger.debug(f"Slack API Response: {json_data}")
        if not json_data.get("ok"):
            logger.error(f"Slack API Error: {json_data.get('error')}")
            raise Exception(f"Slack API Error: {json_data.get('error')}")
        return json_data.get("channels", [])

    @classmethod
    def send_message(cls, message, channel_id, thread_ts=None):
        """
        Slackにメッセージを送信する

        Args:
            message (str): 送信するメッセージ内容
            channel_id (str): 送信先のチャンネルID
            thread_ts (str, optional): スレッドのタイムスタンプ(スレッド返信の場合)
        """
        url = "https://slack.com/api/chat.postMessage"
        payload = {
            "channel": channel_id,  # 送信先のチャンネルIDを指定
            "text": message,
        }
        if thread_ts:
            payload["thread_ts"] = thread_ts

        response = requests.post(url, headers=cls.get_headers(), json=payload)
        response.raise_for_status()
        json_data = response.json()
        if not json_data.get("ok"):
            logger.error(f"Slack API Error: {json_data.get('error')}")
            raise Exception(f"Slack API Error: {json_data.get('error')}")
        return json_data
