import requests
import os
from ....lib.custom_logger import get_logger


logger = get_logger()


class ApiRocketChat:
    """
    RocketChat APIを操作するクラス

    Notes:
        - 環境変数
          - `ROCKET_CHAT_API_URL`, `ROCKET_CHAT_API_KEY`, `ROCKET_CHAT_USER_ID` が必要
        - ユーザーの取得、作成、削除、チャンネルの取得などの基本的な操作を提供します。
    """

    API_URL = os.getenv("ROCKET_CHAT_API_URL") # RocketChatのAPIエンドポイント
    API_KEY = os.getenv("ROCKET_CHAT_API_KEY") # Bearer トークン
    USER_ID = os.getenv("ROCKET_CHAT_USER_ID") # ユーザーID

    @classmethod
    def get_headers(cls):
        """
        APIリクエスト用のヘッダーを取得する
        """
        return {
            "X-Auth-Token": cls.API_KEY,
            "X-User-Id": cls.USER_ID,
            "Content-Type": "application/json",
        }

    @classmethod
    def get_users(cls, limit=100):
        """
        RocketChatのユーザー一覧を取得する

        Args:
            limit (int): 取得するユーザー数の上限

        Returns:
            list: ユーザー情報のリスト
        """
        url = f"{cls.API_URL}/api/v1/users.list?count={limit}"
        response = requests.get(url, headers=cls.get_headers())
        response.raise_for_status()
        json_data = response.json()
        return json_data.get("users", [])

    @classmethod
    def show_user(cls, user_name: str = None, user_id: str = None):
        """
        RocketChatのユーザー情報を取得する

        Args:
            user_id (str): ユーザーのID

        Returns:
            dict: ユーザー情報
        """
        url = f"{cls.API_URL}/api/v1/users.info"
        params = {}
        if user_name:
            params["username"] = user_name
        elif user_id:
            params["userId"] = user_id
        else:
            raise ValueError("Either user_name or user_id must be provided.")

        response = requests.get(url, params=params, headers=cls.get_headers())
        response.raise_for_status()
        return response.json().get("user", {})

    @classmethod
    def delete_user(cls, user_id: str):
        """
        RocketChatのユーザーを削除する

        Args:
            user_id (str): 削除するユーザーのID

        Returns:
            dict: 削除結果の情報
        """
        url = f"{cls.API_URL}/api/v1/users.delete"
        payload = {"userId": user_id}
        response = requests.post(url, headers=cls.get_headers(), json=payload)
        response.raise_for_status()
        return response.json()

    @classmethod
    def create_user(
        cls,
        username: str,
        name: str,
        email: str,
        password: str,
        roles: list = None,
        verified: bool = True,
        require_password_change: bool = False,
    ):
        """
        RocketChatの新しいユーザーを作成する

        Args:
            username (str): ユーザー名
            name (str): ユーザーの表示名
            email (str): メールアドレス
            password (str): パスワード
            roles (list): ユーザーのロール(オプション)
            verified (bool): メールアドレスの検証ステータス(デフォルトはTrue)
            require_password_change (bool): 初回ログイン時のパスワード変更を要求設定
              - デフォルトはFalse

        Returns:
            dict: 作成されたユーザー情報
        """
        url = f"{cls.API_URL}/api/v1/users.create"
        payload = {
            "username": username,
            "name": name,
            "email": email,
            "password": password,
            "verified": verified,
            "requirePasswordChange": require_password_change,
        }
        if roles:
            payload["roles"] = roles

        response = requests.post(url, headers=cls.get_headers(), json=payload)
        response.raise_for_status()
        logger.debug(f"create_user: {response.json()}")
        return response.json().get("user", {})

    @classmethod
    def get_channels(cls):
        """
        RocketChatのチャンネル一覧を取得する

        Returns:
            list: チャンネル情報のリスト
        """
        url = f"{cls.API_URL}/api/v1/channels.list"
        response = requests.get(url, headers=cls.get_headers())
        response.raise_for_status()
        json_data = response.json()
        logger.debug(f"get_channels: {json_data}")
        return json_data.get("channels", [])

    @classmethod
    def get_groups(cls):
        """
        RocketChatのチャンネル一覧(プライベートチャンネル)を取得する

        Returns:
            list: チャンネル情報のリスト
        """
        url = f"{cls.API_URL}/api/v1/groups.list"
        response = requests.get(url, headers=cls.get_headers())
        response.raise_for_status()
        json_data = response.json()
        logger.debug(f"get_groups: {json_data}")
        return json_data.get("channels", [])
