import os
import requests


class ApiHotpepperGourmet:
    """
    ホットペッパーグルメAPIクライアント
    """
    RECRUIT_API_KEY = os.getenv("RECRUIT_API_KEY")
    HOTPEPPER_API_URL = "http://webservice.recruit.co.jp/hotpepper"

    def search(self, params: dict) -> dict:
        """
        グルメ検索APIを呼び出します。

        Parameters:
            params (dict): 検索パラメータ
                - id (str): 店舗ID
                - name_any (str): 店舗名
                - lat (float): 緯度
                - lng (float): 経度
                - tel (str): お店の電話番号で検索します。半角数字(ハイフンなし)
                - keyword (str): キーワード
                - range (int): 検索範囲(1: 500m, 2: 1000m, 3: 3000m, 4: 5000m)
                - count (int): 取得件数
        Returns:
            dict: レスポンス(JSON形式)
        """
        query = {
            "key": self.RECRUIT_API_KEY,
            "format": "json",  # JSON指定
            **params,
        }
        response = requests.get(f"{self.HOTPEPPER_API_URL}/gourmet/v1", params=query)
        response.raise_for_status()
        return response.json()
