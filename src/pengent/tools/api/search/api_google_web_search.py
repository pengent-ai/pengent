import os
import time
from googleapiclient.discovery import build


class ApiGoogleWebSearch:
    """Google Web Search APIクライアント"""
    GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
    GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")

    @classmethod
    def search(cls, query: str, page_limit=1, limit=10, start_index=1):
        """
        Google Web Search APIを使用して検索するメソッド
        Args:
            query (str): 検索クエリ
            page_limit (int): 取得するページ数
            limit (int): 1ページあたりの取得件数
            start_index (int): 開始インデックス

        Returns:
            list: 検索結果のリスト
        """
        if not cls.GOOGLE_SEARCH_API_KEY or not cls.GOOGLE_SEARCH_ENGINE_ID:
            raise ValueError("APIキーまたは検索エンジンIDが設定されていません")

        service = build("customsearch", "v1", developerKey=cls.GOOGLE_SEARCH_API_KEY)

        response_list = []
        for _ in range(page_limit):
            try:
                time.sleep(1)
                result = (
                    service.cse()
                    .list(
                        q=query,
                        cx=cls.GOOGLE_SEARCH_ENGINE_ID,
                        lr="lang_ja",
                        num=limit,
                        start=start_index,
                    )
                    .execute()
                )

                response_list.append(result)

                # 次ページがなければ終了
                next_page = result.get("queries", {}).get("nextPage")
                if not next_page:
                    break

                start_index = next_page[0].get("startIndex")
            except Exception as e:
                print(f"[ERROR] {e}")
                break

        return response_list
