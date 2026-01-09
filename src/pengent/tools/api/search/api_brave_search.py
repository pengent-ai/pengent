import os
import requests
from ....lib.custom_logger import get_logger

logger = get_logger()


class ApiBraveSearch:
    """
    A class to interact with the Brave Search API.

    Notes:

    """

    BRAVE_SEARCH_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY")
    BRAVE_SEARCH_API_URL = "https://api.search.brave.com/res/v1/web"

    @classmethod
    def search(cls, query: str, limit: int = 10, start: int = 0, country: str = "JP"):
        """
        Brave Search APIを使用してWEBページを検索するメソッド

        Args:
            query (str): 検索クエリ
            limit (int): 取得する件数
            start (int): 開始インデックス

        Returns:
            list: 検索結果のリスト
        """

        if not cls.BRAVE_SEARCH_API_KEY:
            raise ValueError("APIキーが設定されていません")

        url = f"{cls.BRAVE_SEARCH_API_URL}/search"
        headers = {
            "X-Subscription-Token": f"{cls.BRAVE_SEARCH_API_KEY}",
            "Accept-Encoding": "gzip",
            "Accept": "application/json",
        }
        params = {
            "q": query,
            "count": limit,
            "offset": start,
            "country": country,  # 日本の検索結果を取得
        }
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        logger.debug(f"Brave Search API Response: {response.status_code}")
        json_data = response.json()
        return json_data.get("web", {}).get("results", [])
