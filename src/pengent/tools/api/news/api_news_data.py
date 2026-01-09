import requests
import os
from ....lib.custom_logger import get_logger


logger = get_logger()


class ApiNewsData:
    """
    NewsData APIを操作するクラス

        Notes:
        - NewsData APIを使用してニュース記事を取得するためのクラス
        - APIキーは環境変数 `NEWS_DATA_API_KEY` から取得されます
        - 詳細なAPIドキュメントは https://newsdata.io/docs/api を参照してください
    """

    NEWS_DATA_API_KEY = os.getenv("NEWS_DATA_API_KEY")

    @classmethod
    def get_news(
        cls,
        language: str = "jp",
        country: str = "jp",
        category: str = None,
    ):
        """
        NewsData APIを使用してニュース記事を取得する

        Args:
            language (str): 記事の言語コード (例: "ja" = 日本語)
            country (str): 国コード (例: "jp" = 日本)
            category (str): カテゴリコード (例: "business", "technology", "sports" など)

        Returns:
            list: ニュース記事のリスト
        """
        # url = "https://newsdata.io/api/1/news"
        url = "https://newsdata.io/api/1//latest"
        params = {
            "apikey": cls.NEWS_DATA_API_KEY,
            "language": language,
            "country": country,
        }
        if category:
            params["category"] = category

        response = requests.get(url, params=params)
        response.raise_for_status()
        json_data = response.json()
        if not json_data.get("status") == "success":
            logger.error(f"NewsData API Error: {json_data.get('message')}")
            raise Exception(f"NewsData API Error: {json_data.get('message')}")
        logger.debug(f"NewsData API Response: {json_data}")
        return json_data.get("results", [])
