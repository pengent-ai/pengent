import os
import requests
from ....lib.custom_logger import get_logger
from .api_git_base import ApiGitBase
from typing import List

logger = get_logger()


class ApiGithub(ApiGitBase):
    """
    GitHubAPIのベースクラス

    Notes:
        - Github API Docs: https://docs.github.com/en/rest?apiVersion=2022-11-28
    """

    _API_URL = "https://api.github.com"
    _API_KEY = os.getenv("GITHUB_API_KEY")

    def _get_headers(self) -> dict:
        """
        ヘッダー情報を取得する

        Returns:
            dict: APIリクエスト用のヘッダー情報
        """
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._API_KEY}",
        }
        return headers

    def search_repo(
        self, query: str, sorting: str = "best match", page: int = 1, per_page: int = 10
    ) -> List[dict]:
        """
        リポジトリを検索する

        Args:
            query (str): 検索クエリ
            sorting (str): ソート方法(デフォルトは"best match")
            page (int): ページ番号
            per_page (int): 1ページあたりのアイテム数

        Returns:
            List[dict]: 検索結果のリポジトリ情報
        """
        url = f"{self._API_URL}/search/repositories"
        params = {"q": query, "sort": sorting, "page": page, "per_page": per_page}
        headers = self._get_headers()
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        logger.info(
            "Searching repositories with query: "
            f"{query}, page: {page}, per_page: {per_page}"
        )
        return response.json().get("items", [])

    def search_code(
        self,
        query: str,
        page: int = 1,
        per_page: int = 30,
        repo: str = None,
        language: str = None,
        filename: str = None,
    ):
        """
        コードを検索する
        Args:
            query (str): 検索クエリ
            page (int): ページ番号
            per_page (int): 1ページあたりのアイテム数
            repo (str, optional): リポジトリ名(例: "owner/repo")
            language (str, optional): 言語フィルター
            filename (str, optional): ファイル名フィルター
        Returns:
            List[dict]: 検索結果のコード情報
        """
        url = f"{self._API_URL}/search/code"
        q_parts = []
        if query:
            q_parts.append(query)
        if repo:
            q_parts.append(f"repo:{repo}")
        if language:
            q_parts.append(f"language:{language}")
        if filename:
            q_parts.append(f"filename:{filename}")

        # クエリをスペース区切りで結合(GitHub APIの仕様)
        q = " ".join(q_parts)
        params = {"q": q, "page": page, "per_page": per_page}
        headers = self._get_headers()
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        logger.info(
            f"Searching code with query: {query}, page: {page}, per_page: {per_page}"
        )
        return response.json().get("items", [])
