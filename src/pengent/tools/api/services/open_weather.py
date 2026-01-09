import os
import requests

from ....lib.custom_logger import get_logger

logger = get_logger()
import json


class ApiOpenWeatherMap:
    """
    天気情報を取得するためのAPIクライアント

    Reference:
        https://openweathermap.org
    """

    _API_URL = "https://api.openweathermap.org"
    _API_KEY = os.getenv("OPEN_WEATHER_API_KEY")

    # キャッシュを外部ファイルからロード
    _CACHE_FILE = os.getenv(
        "OPEN_WEATHER_CACHE_FILE", ".storage/default/.api_cache.json"
    )  # ファイル名環境変数から指定も可能
    _API_CACHE = {}

    try:
        if os.path.exists(_CACHE_FILE):
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                _API_CACHE = json.load(f)
                logger.debug(f"Loaded API cache from {_CACHE_FILE}")
        else:
            logger.debug("No cache file found. Starting with empty cache.")
    except Exception as e:
        logger.warning(f"Failed to load API cache: {e}")
        _API_CACHE = {}

    @classmethod
    def geocoding(cls, q: str, limit: int = None) -> dict:
        """
        指定した都市名の緯度と経度を取得するメソッド

        Args:
            q (str): 都市名(例: "Tokyo")
            limit (int): 取得する結果の数(デフォルトは5)

        Returns:
            dict: 緯度と経度を含む辞書
        """
        uri = "/geo/1.0/direct"

        # ヘッダー情報を設定
        headers = {"Content-Type": "application/json"}

        # GETリクエストを送信
        response = requests.get(
            f"{cls._API_URL}{uri}",
            headers=headers,
            params={"q": q, "appid": cls._API_KEY, "limit": limit},
        )
        response.raise_for_status()
        json_data = response.json()
        logger.debug(
            f"success q: {q} lat: {json_data[0].get('lat')} "
            f"lon: {json_data[0].get('lon')} "
        )
        return json_data

    @classmethod
    def write_cache(cls):
        """
        キャッシュをファイルに書き込むメソッド
        """
        try:
            # ここで親ディレクトリを作成
            os.makedirs(os.path.dirname(cls._CACHE_FILE), exist_ok=True)
            with open(cls._CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cls._API_CACHE, f, ensure_ascii=False, indent=4)
            logger.debug(f"Cache written to {cls._CACHE_FILE}")
        except Exception as e:
            logger.warning(f"Failed to write cache: {e}")
