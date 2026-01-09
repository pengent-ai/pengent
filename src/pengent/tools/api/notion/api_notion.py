import requests
import os
from ....lib.custom_logger import get_logger
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

logger = get_logger()


# @dataclass
class NotionBlockType(str, Enum):
    """
    Notionのブロックタイプを定義するEnum
    """

    PARAGRAPH = "paragraph"
    HEADING_1 = "heading_1"
    HEADING_2 = "heading_2"
    HEADING_3 = "heading_3"
    CODE = "code"
    BULLETED_LIST_ITEM = "bulleted_list_item"
    NUMBERED_LIST_ITEM = "numbered_list_item"
    TOGGLE = "toggle"
    QUOTE = "quote"
    DIVIDER = "divider"
    IMAGE = "image"


@dataclass
class NotionText:
    """
    Notionのテキストオブジェクトを表すデータクラス
    """
    content: str
    link: Optional[str] = None

    def to_dict(self):
        text_dict = {"type": "text", "text": {"content": self.content}}
        if self.link:
            text_dict["text"]["link"] = {"url": self.link}
        return text_dict


@dataclass
class NotionRichText:
    """
    Notionのリッチテキストを表すデータクラス
    """
    text: NotionText

    def to_dict(self):
        return self.text.to_dict()


@dataclass
class NotionBlock:
    """
    Notionのブロックを表すデータクラス
    """
    block_type: NotionBlockType = NotionBlockType.PARAGRAPH
    rich_text: List[NotionRichText] = field(default_factory=list)
    language: Optional[str] = None  # コードブロック用の言語
    caption: List[NotionRichText] = None
    color: Optional[str] = None  # ブロックの色(例: "default", "gray", "brown"など)
    children: List["NotionBlock"] = field(default_factory=list)  # 子ブロックのリスト

    def to_dict(self):
        """
        ブロックを辞書形式に変換する
        """
        ret = {
            "object": "block",
            "type": self.block_type.value,
            self.block_type.value: {
                "rich_text": [rt.to_dict() for rt in self.rich_text]
            },
        }
        if self.block_type == NotionBlockType.CODE:
            if self.language:
                ret[self.block_type.value]["language"] = self.language
            if self.caption:
                ret[self.block_type.value]["caption"] = [
                    rt.to_dict() for rt in self.caption
                ]

        if (
            self.block_type == NotionBlockType.BULLETED_LIST_ITEM
            or self.block_type == NotionBlockType.NUMBERED_LIST_ITEM
        ):
            if self.color:
                ret[self.block_type.value]["color"] = self.color
            if self.children:
                ret[self.block_type.value]["children"] = [
                    child.to_dict() for child in self.children
                ]

        return ret

    @classmethod
    def create_pharagraph_block(cls, text: str, link: Optional[str] = None):
        """
        段落ブロックを作成する
        """
        return cls(
            block_type=NotionBlockType.PARAGRAPH,
            rich_text=[NotionRichText(text=NotionText(content=text, link=link))],
        )

    @classmethod
    def create_heading_block(cls, text: str, level: int = 1):
        """
        見出しブロックを作成する
        """
        if level == 1:
            block_type = NotionBlockType.HEADING_1
        elif level == 2:
            block_type = NotionBlockType.HEADING_2
        elif level == 3:
            block_type = NotionBlockType.HEADING_3
        else:
            raise ValueError("level must be 1, 2, or 3 for headings.")

        return cls(
            block_type=block_type,
            rich_text=[NotionRichText(text=NotionText(content=text))],
        )

    @classmethod
    def create_code_block(
        cls,
        text: str,
        language: Optional[str] = None,
        catption: Optional[List[NotionRichText]] = None,
    ):
        """
        コードブロックを作成する
        """
        return cls(
            block_type=NotionBlockType.CODE,
            rich_text=[NotionRichText(text=NotionText(content=text))],
            language=language,
            caption=catption,
        )

    @classmethod
    def create_bulleted_list_item(cls, text: str, color="default", children=None):
        return cls(
            block_type=NotionBlockType.BULLETED_LIST_ITEM,
            rich_text=[NotionRichText(text=NotionText(content=text))],
            color=color,
            children=children,
        )


@dataclass
class NotionPage:
    """
    Notionのページ情報を表すデータクラス
    """
    title: str = ""
    parent_type: str = "page"  # 親のタイプ(例: "page", "database")
    page_id: str = None
    database_id: str = None
    parent_page_id: str = None  # 親ページのID
    children: List = field(default_factory=list)  # 子ページのIDリスト
    properties: dict = field(default_factory=dict)

    def get_parent(self):
        """
        ペアレントページ情報を取得する
        """
        if self.parent_type == "database":
            return {"database_id": self.database_id}
        elif self.parent_type == "page":
            return {"page_id": self.parent_page_id}
        else:
            raise ValueError(
                f"Unsupported parent_type: {self.parent_type}. "
                "Must be 'page' or 'database'."
            )

    def get_properties(self):
        """
        ページのプロパティを取得する
        """
        if self.parent_type == "page":
            return {"title": {"title": [{"text": {"content": self.title}}]}}
        elif self.parent_type == "database":
            return self.properties


class ApiNotion:
    """
    Notion APIを操作するクラス

    Notes:
        - Notion APIの使用にはAPIキーが必要です。
          - 環境変数 `NOTION_API_KEY` に設定してください。
        - APIのエンドポイントは `https://api.notion.com/v1` です。
        - https://developers.notion.com/reference/post-database-query-filter
        - https://www.notion.so/my-integrations

    """

    API_URL = "https://api.notion.com/v1"
    API_KEY = os.getenv("NOTION_API_KEY")  # Bearer トークン

    @classmethod
    def get_headers(cls):
        """
        APIリクエスト用のヘッダーを取得する
        """
        return {
            "Authorization": f"Bearer {cls.API_KEY}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

    @classmethod
    def search(cls, filter="page", prop="object"):
        """
        Notionのデータベースを検索する

        Args:
            filter (str): 検索フィルターの種類
            prop (str): プロパティの種類

        Returns:
            List[dict]: 検索結果のリスト
        """
        headers = cls.get_headers()

        url = f"{cls.API_URL}/search"
        payload = {"filter": {"property": prop, "value": filter}}

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        json_data = response.json()
        logger.debug(f"search result: {json_data}")
        return json_data.get("results", [])

    @classmethod
    def show_page(cls, page_id: str) -> dict:
        """
        Notionのページを取得する

        Args:
            page_id (str): ページのID
        """
        headers = cls.get_headers()
        url = f"{cls.API_URL}/pages/{page_id}"

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        json_data = response.json()
        logger.debug(f"show_page result: {json_data}")
        return json_data

    @classmethod
    def create_database(cls, page_id: str, title: str, properties: dict):
        """
        Notionに新しいデータベースを作成する

        Args:
            page_id (str): 親ページのID
            title (str): データベースのタイトル
            proparties (dict): データベースのプロパティ

        Returns:
            dict: 作成されたデータベースの情報
        """
        headers = cls.get_headers()
        url = f"{cls.API_URL}/databases"

        payload = {
            "parent": {"type": "page_id", "page_id": page_id},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": properties,
        }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    @classmethod
    def create_page(
        cls,
        page: NotionPage,
    ):
        """
        Notionに新しいページを作成する

        Args:
            page (NotionPage): 作成するページの情報

        Returns:
            dict: 作成されたページの情報
        """
        headers = cls.get_headers()
        url = f"{cls.API_URL}/pages"

        payload = {
            "parent": page.get_parent(),  # 親ページの情報
            "properties": page.get_properties(),
        }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    @classmethod
    def update_page_properties(cls, page: NotionPage):
        """
        Notionのページのプロパティを更新する

                Args:
            page (NotionPage): 更新するページの情報
        """
        if page.page_id is not None:
            raise ValueError("page_id should be None for creating a new page.")

        headers = cls.get_headers()
        url = f"{cls.API_URL}/pages/{page.page_id}"

        payload = {"properties": page.get_properties()}
        response = requests.patch(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    @classmethod
    def delete_page(cls, page: NotionPage):
        """
        Notionのページを削除する

        Args:
            page (NotionPage): 削除するページの情報
        """
        if page.page_id is not None:
            raise ValueError("page_id should be None for creating a new page.")

        headers = cls.get_headers()
        url = f"{cls.API_URL}/pages/{page.page_id}"

        payload = {
            "archived": True,  # ページをアーカイブする
        }
        response = requests.patch(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    @classmethod
    def get_blocks(cls, block_id: str) -> dict:
        """
        Notionのページのブロックを取得する
        Args:
            block_id (str): ブロックのID
        Returns:
            dict: ブロックの情報
        """
        headers = cls.get_headers()
        url = f"{cls.API_URL}/blocks/{block_id}/children"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        json_data = response.json()
        logger.debug(f"get_blocks result: {json_data}")
        return json_data.get("results", [])

    @classmethod
    def add_blocks(cls, block_id: str, blocks: List[NotionBlock]) -> dict:
        """
        Notionのページにブロックを追加する

        Args:
            block_id (str): ページのID
            blocks (List[NotionBlock]): 追加するブロックのリスト

        Returns:
            dict: 追加されたブロックの情報
        """
        headers = cls.get_headers()
        url = f"{cls.API_URL}/blocks/{block_id}/children"

        payload = {"children": [block.to_dict() for block in blocks]}
        logger.debug(f"add_blocks payload: {payload}")

        # Notion APIの仕様に合わせて、ブロックのリストを辞書形式に変換

        response = requests.patch(url, json=payload, headers=headers)
        response.raise_for_status()
        logger.debug(f"add_blocks result: {response.json()}")
        return response.json()
