import requests
import os
from ....lib.custom_logger import get_logger
from dataclasses import dataclass, field
from typing import List
from collections import Counter

logger = get_logger()


@dataclass
class ApiQiitaTag:
    """
    Qiita APIで使用されるタグ情報を表現するクラス。

    Attributes:
        name (str): タグ名(例: "Python")
        versions (List[str]): バージョン情報(例: ["3.10"])

    Examples:
        >>> tag = ApiQiitaTag(name="Python")
        >>> tag.to_dict()
        {'name': 'Python', 'versions': []}

        >>> tag2 = ApiQiitaTag.from_dict({"name": "API", "versions": ["v2"]})
        >>> tag2.name
        'API'
        >>> tag2.versions
        ['v2']
    """

    name: str
    versions: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """
        インスタンスを辞書形式に変換する。

        Returns:
            dict: {"name": ..., "versions": [...]}
        """
        return {"name": self.name, "versions": self.versions}

    @classmethod
    def from_dict(cls, data: dict) -> "ApiQiitaTag":
        """
        辞書からインスタンスを生成する。

        Args:
            data (dict): {"name": ..., "versions": [...]}

        Returns:
            ApiQiitaTag: インスタンス

        Examples:
            >>> ApiQiitaTag.from_dict({"name": "Python", "versions": ["3.11"]}).name
            'Python'
        """
        return cls(name=data.get("name", ""), versions=data.get("versions", []))


class ApiQiita:
    """
    Qiita APIクライアント
    """
    API_URL = "https://qiita.com"
    API_KEY = os.getenv("QIITA_API_KEY")  # Bearer トークン

    @classmethod
    def get_posts(cls, page=1, per_page=10, tag_query: str = None, stocks_over=None):
        """
        Qiitaの記事一覧を取得するメソッド

        Args:
            page (int): ページ番号
            per_page (int): 1ページあたりの記事数
            tag_query (str): タグで絞り込むクエリ(例: "Python")
            stocks_over (int): ストック数の上限(例: 10) 人気記事を指定できる
        Returns:
            list: Qiitaの記事情報のリスト
        References:
            - Qiita API v2 Docs: https://qiita.com/api/v2/docs
        """
        logger.info(f"get posts from Qiita: page={page}, per_page={per_page}")
        uri = "/api/v2/items"

        params = {"page": page, "per_page": per_page}

        if tag_query:
            params["query"] = f"tag:{tag_query}"
        if stocks_over is not None:
            if params.get("query"):
                params["query"] += f" stocks:>={stocks_over}"
            else:
                params["query"] = f"stocks:>={stocks_over}"

        headers = {
            "Authorization": f"Bearer {cls.API_KEY}",
            "Content-Type": "application/json",
        }

        response = requests.get(f"{cls.API_URL}{uri}", params=params, headers=headers)
        response.raise_for_status()
        logger.info(f"get posts from Qiita success: {response.status_code}")
        json_data = response.json()
        return json_data

    @classmethod
    def get_tags(cls, page=1, per_page=50):
        """
        Qiitaのタグ一覧を取得するメソッド

        Args:
            page (int): ページ番号
            per_page (int): 1ページあたりのタグ数
        Returns:
            list: Qiitaのタグ情報のリスト
        References:
            - Qiita API v2 Docs: https://qiita.com/api/v2/docs
        """
        logger.info(f"get tags from Qiita: page={page}, per_page={per_page}")
        uri = "/api/v2/tags"
        params = {"page": page, "per_page": per_page}
        headers = {
            "Authorization": f"Bearer {cls.API_KEY}",
            "Content-Type": "application/json",
        }

        response = requests.get(f"{cls.API_URL}{uri}", params=params, headers=headers)
        response.raise_for_status()
        logger.info(f"get tags from Qiita success: {response.status_code}")
        json_data = response.json()
        return json_data

    @classmethod
    def get_trend_tags(
        cls, page=1, per_page=50, tag_query: str = None, stocks_over=20, limit=10
    ):
        """
        Qiitaのトレンドタグ一覧を取得するメソッド

        Args:
            page (int): ページ番号
            per_page (int): 1ページあたりの記事数
            tag_query (str): タグで絞り込むクエリ(例: "Python")
            stocks_over (int): ストック数の上限(例: 50) 人気記事を指定できる
            limit(int): 取得するタグの数(デフォルトは10)
        Returns:
            list: Qiitaのトレンドタグ情報のリスト
        References:
            - Qiita API v2 Docs: https://qiita.com/api/v2/docs
        """
        logger.info(f"get trend tags from Qiita: page={page}, per_page={per_page}")
        # 記事を取得する
        articles = cls.get_posts(
            page=page, per_page=per_page, tag_query=tag_query, stocks_over=stocks_over
        )

        tag_counter = Counter()
        for article in articles:
            for tag in article.get("tags", []):
                tag_counter[tag["name"]] += 1
        trand_tags = tag_counter.most_common()
        logger.info(f"get trend tags from Qiita success: {len(trand_tags)} tags found")
        # タグの出現回数を降順でソート
        sorted_tags = sorted(trand_tags, key=lambda x: x[1], reverse=True)
        # 指定された数だけ取得
        if limit:
            tags = sorted_tags[:limit]
        return tags

    @classmethod
    def post(
        cls,
        title,
        content,
        tags: list = None,
        private=True,
        coediting=False,
        gist=False,
        tweet=False,
    ):
        """
        Qiitaに記事を投稿するメソッド

        Args:
            title (str): 記事のタイトル
            content (str): Markdown形式の記事内容
            tags (list[ApiQiitaTag]): タグ
              - 例: [ApiQiitaTag(name="Python", versions=["3.10"]),]
            private (bool): プライベートページかどうか
            coediting (bool): コラボレーション編集を許可するかどうか
            gist (bool): Gistとして公開するかどうか
            tweet (bool): Twitterに投稿するかどうか
        References:
            - Qiita API v2 Docs: https://qiita.com/api/v2/docs#post-apiv2items
        """
        if tags is None:
            tags = []
        logger.info(f"post to Qiita: {title}")
        uri = "/api/v2/items"

        headers = {
            "Authorization": f"Bearer {cls.API_KEY}",
            "Content-Type": "application/json",
        }

        # Rest API Post
        post = {
            "title": title,
            "body": content,
            "tags": [tag.to_dict() for tag in tags],
            "private": private,
            "coediting": coediting,
            "gist": gist,
            "tweet": tweet,
        }

        response = requests.post(f"{cls.API_URL}{uri}", json=post, headers=headers)
        response.raise_for_status()

        json_data = response.json()
        logger.info(f"post to wiki.js success: {json_data}")
        article_url = json_data.get("url")
        logger.info(f"create url: {article_url}")
        return json_data

    @classmethod
    def put(
        cls,
        item_id,
        title,
        content,
        tags: list = None,
        private=True,
        coediting=False,
        gist=False,
        tweet=False,
    ):
        """
        Qiitaに記事を更新するメソッド

        Args:
            item_id (str): 記事のID
            title (str): 記事のタイトル
            content (str): Markdown形式の記事内容
            tags (list[ApiQiitaTag]): タグ
              - 例: [ApiQiitaTag(name="Python", versions=["3.10"])])
            private (bool): プライベートページかどうか
            coediting (bool): コラボレーション編集を許可するかどうか
            gist (bool): Gistとして公開するかどうか
            tweet (bool): Twitterに投稿するかどうか
        Notes:
            - 全項目を上書きする仕様なので、すべての必須フィールドを送る必要がある。
        References:
            - Qiita API v2 Docs: https://qiita.com/api/v2/docs
        """
        if tags is None:
            tags = []
        logger.info(f"put to Qiita: {title}")
        uri = f"/api/v2/items/{item_id}"

        headers = {
            "Authorization": f"Bearer {cls.API_KEY}",
            "Content-Type": "application/json",
        }

        # Rest API Post
        post = {
            "title": title,
            "body": content,
            "tags": [tag.to_dict() for tag in tags],
            "private": private,
            "coediting": coediting,
            "gist": gist,
            "tweet": tweet,
        }

        response = requests.patch(f"{cls.API_URL}{uri}", json=post, headers=headers)
        response.raise_for_status()

        json_data = response.json()
        logger.info(f"post to wiki.js success: {json_data}")
        article_url = json_data.get("url")
        logger.info(f"create url: {article_url}")
        return json_data
