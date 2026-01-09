import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
)

from pengent.lib import get_logger

logger = get_logger(level=10)

from dotenv import load_dotenv

load_dotenv()

from pengent.tools.api.notion.api_notion import ApiNotion, NotionPage #, NotionBlock


def example_notion():
    api = ApiNotion()
    # res = api.search()
    # res = api.show_page("2067b7e8652080b3a2f3eacf104fb5b3")
    # res = api.create_page(page)
    page = NotionPage(
        # page_id="2067b7e8652081fba692d758093a23a2"
        page_id="2067b7e865208026a79cca60e6b70aba"
    )
    # blocks = [
    #     NotionBlock.create_pharagraph_block(
    #         "📄 Page: Notionの基本単位で、テキストやブロックを含むドキュメントです"
    #     ),
    #     NotionBlock.create_pharagraph_block(
    #         "🧱 Block: ページを構成する最小単位で、段落や見出しなどがあります"
    #     ),
    #     NotionBlock.create_pharagraph_block(
    #         "📊 Database: "
    #         "テーブル形式などで構造化されたデータを管理するNotionの高機能なページです"
    #     ),
    #     NotionBlock.create_heading_block("Blockについて", 2),
    #     NotionBlock.create_pharagraph_block(
    #         "Notionの基本的なブロックの使い方を説明します"
    #     ),
    #     NotionBlock.create_bulleted_list_item("Headline"),
    #     NotionBlock.create_bulleted_list_item("Paragraph"),
    #     NotionBlock.create_bulleted_list_item("BulletedListItem"),
    #     NotionBlock.create_heading_block("Databaseについて", 2),
    #     NotionBlock.create_pharagraph_block(
    #         "Notionのデータベースは、厳密スキーマやトランザクション機能ない、"
    #         "直感的なUIと柔軟なデータ構造により、"
    #         "情報整理や簡易アプリケーションの構築に適しています。"
    #     ),
    #     NotionBlock.create_pharagraph_block(
    #         "各レコードは「ページ」として扱われ、プロパティ(列)で情報を管理しながら、"
    #         "ページ内にはテキストや画像、コードなどのブロックを自由に追加できる。"
    #     ),
    #     NotionBlock.create_pharagraph_block(
    #         "ただし、大量データの検索・集計や複雑なリレーションには向いておらず、"
    #         "外部DBとの併用やAPI連携による補完が必要になるケースもあります。"
    #     ),
    #     NotionBlock.create_pharagraph_block(
    #         "また、削除は「アーカイブ」という形式で行われ、完全削除には非対応です。"
    #         "更新や検索にはNotion APIを用いますが、パフォーマンスでは制約があります。"
    #     ),
    # ]
    # res = api.add_blocks(page.page_id,blocks)
    properties = {
        "Name": {"title": {}},
        "Description": {"rich_text": {}},
        "Status": {
            "select": {"options": [{"name": "In Progress"}, {"name": "Completed"}]}
        },
        "Request ID": {"rich_text": {}},
    }
    res = api.create_database(page.page_id, "AI Requests", properties=properties)
    logger.debug(f"res: {res}")


def example_database():
    database_id = "2067b7e8-6520-8199-9937-db0ec23225fa"
    # DBを作成する時はCreatePageで作成する必要がある
    api = ApiNotion()
    page = NotionPage(
        database_id=database_id,
        parent_type="database",
        properties={
            "Name": {"title": [{"text": {"content": "Test Request"}}]},
            "Description": {
                "rich_text": [
                    {"text": {"content": "This is a test request for AI development."}}
                ]
            },
            "Status": {"select": {"name": "In Progress"}},
            "Request ID": {"rich_text": [{"text": {"content": "Test_Request"}}]},
        },
    )
    res = api.create_page(page)
    logger.debug(f"res: {res}")


# example_notion()
example_database()
