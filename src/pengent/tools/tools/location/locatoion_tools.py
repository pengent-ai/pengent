from ....tools.tool_utils import tool
from ...api.services.open_weather import ApiOpenWeatherMap
from ....lib.custom_logger import get_logger

logger = get_logger()


class LocationTools:
    """ロケーションに関するツール群を提供するクラス

    Notes:
        - OpenWeatherMap 都市名から緯度・経度を取得する機能を提供します。
    See Also:
        - APIキーの取得・設定は利用者側で行う必要があります。
        - 外部APIの制限・仕様変更により、取得できる情報が変動する可能性あり
        - pengent/tools/api/services/open_weather.py
    """

    @staticmethod
    @tool(tags=["location"])
    def geocoding(location: str):
        """
        指定した都市名の緯度と経度を取得するメソッド

        Parameters:
            location (str): 都市名  (例: "Tokyo")

        Reference:
            https://home.openweathermap.org/users/sign_up
        """
        city_cache = ApiOpenWeatherMap._API_CACHE.get("geocoding", {})
        if location in city_cache:
            logger.debug(f"cache hit: {location}")
            return city_cache[location]

        res = ApiOpenWeatherMap.geocoding(location, limit=1)
        if res:
            data = res[0]
            temp = {"lat": data["lat"], "lon": data["lon"], "country": data["country"]}
            city_cache[location] = temp
            ApiOpenWeatherMap._API_CACHE["geocoding"] = city_cache
            ApiOpenWeatherMap.write_cache()

            return city_cache[location]
