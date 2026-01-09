import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
)

from pengent.lib import get_logger

logger = get_logger(level=10)

from dotenv import load_dotenv

load_dotenv()

from pengent.tools.api.news.api_news_data import ApiNewsData


def example():
    api = ApiNewsData()
    res = api.get_news(
        category="technology",  # カテゴリを指定
    )
    for article in res:
        # print(article)
        logger.info(
            f"Title: {article['title']} URL: {article['link']}\n"
            "description: {article['description']}"
        )


example()
