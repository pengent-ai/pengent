import requests
import os
from ....lib.custom_logger import get_logger

logger = get_logger()


class ApiWikiJS:
    """
    Wiki.js APIクライアント(GraphQL)
    """
    API_URL = os.getenv("WIKI_JS_API_URL")  # 例: "https://wiki.example.com/graphql"
    API_KEY = os.getenv("WIKI_JS_API_KEY")  # Bearer トークン

    @classmethod
    def post(
        cls,
        title,
        content,
        path: str = "/",
        locale: str = "en",
        tags: list[str] = None,
        description: str = "",
        editor: str = "markdown",
        is_private: bool = False,
    ):
        """
        Wiki.jsに記事を投稿するメソッド(GraphQL)

        Args:
            title (str): 記事のタイトル
            content (str): Markdown形式の記事内容
            path (str): 記事のパス(例: "/my-article")
            locale (str): ロケール(例: "en", "ja")
            tags (list[str]): タグ(例: ["API", "Python"])
            description (str): 記事の説明
            editor (str): エディターの種類(例: "markdown")
            is_private (bool): プライベートページかどうか
        """
        logger.info(f"post to wiki.js: {title}")

        headers = {
            "Authorization": f"Bearer {cls.API_KEY}",
            "Content-Type": "application/json",
        }

        # GraphQL mutation with variables
        query = """
        mutation CreatePage($title: String!, $content: String!, $description: String!, $editor: String!, $isPublished: Boolean!, $isPrivate: Boolean!, $locale: String!, $path: String!, $tags: [String]!) {
          pages {
            create(
              title: $title,
              content: $content,
              description: $description,
              editor: $editor,
              isPublished: $isPublished,
              isPrivate: $isPrivate,
              locale: $locale,
              path: $path,
              tags: $tags
            ) {
              responseResult {
                succeeded
                errorCode
                slug
                message
              }
              page {
                id
                title
                path
              }
            }
          }
        }
        """ # noqa: E501

        variables = {
            "title": title,
            "content": content,
            "description": description,
            "editor": editor,
            "isPublished": True,
            "isPrivate": is_private,
            "locale": locale,
            "path": path,
            "tags": tags or [],
        }

        response = requests.post(
            cls.API_URL, json={"query": query, "variables": variables}, headers=headers
        )

        if response.status_code == 200:
            json_data = response.json()
            if "errors" in json_data:
                raise Exception(f"GraphQL errors: {json_data['errors']}")
            logger.info(f"post to wiki.js success: {json_data}")
            logger.info(f"create url: {cls.API_URL}/{locale}/{path}")
            return json_data["data"]["pages"]["create"]
        else:
            raise Exception(f"Failed to post: {response.status_code} - {response.text}")

    @classmethod
    def search(cls, keyword: str, locale: str = "en"):
        """
        ページ一覧を取得し、タイトルにキーワードが含まれるものをフィルタリング

        Args:
            keyword (str): 検索キーワード
            locale (str): ロケール

        Returns:
            list: 検索結果(タイトルに keyword を含むページのリスト)
        """
        logger.info(f"search wiki.js title contains: {keyword}")

        headers = {
            "Authorization": f"Bearer {cls.API_KEY}",
            "Content-Type": "application/json",
        }

        query = """
        query SearchPages($q: String!, $locale: String!) {
          pages {
            search(query: $q, locale: $locale) {
              results {
                id      # 検索結果ID(ページIDとは限らない)
                title
                path
                description
                locale
              }
              totalHits
              suggestions
            }
          }
        }
        """
        variables = {"q": keyword, "locale": locale}
        response = requests.post(
            cls.API_URL, json={"query": query, "variables": variables}, headers=headers
        )

        if response.status_code == 200:
            json_data = response.json()
            logger.debug(f"search wiki.js response: {json_data}")
            if "errors" in json_data:
                raise Exception(f"GraphQL errors: {json_data['errors']}")

            pages = json_data["data"]["pages"]["search"]["results"]
            results = [
                page for page in pages if keyword.lower() in page["title"].lower()
            ]
            return results
        else:
            raise Exception(
                f"Failed to search: {response.status_code} - {response.text}"
            )

    @classmethod
    def show(cls, page_id: int):
        logger.info(f"get wiki.js page by id: {page_id}")

        headers = {
            "Authorization": f"Bearer {cls.API_KEY}",
            "Content-Type": "application/json",
        }

        query = """
        query GetPage($id: Int!) {
          pages {
            single(id: $id) {
              id
              title
              path
              content
              description
              tags {
                id
              }
              locale
              editor
            }
          }
        }
        """

        variables = {"id": page_id}

        response = requests.post(
            cls.API_URL, json={"query": query, "variables": variables}, headers=headers
        )

        if response.status_code == 200:
            json_data = response.json()
            if "errors" in json_data:
                raise Exception(f"GraphQL errors: {json_data['errors']}")
            return json_data["data"]["pages"]["single"]
        else:
            raise Exception(
                f"Failed to get page: {response.status_code} - {response.text}"
            )
