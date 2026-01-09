import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
)

from pengent.lib import get_logger

logger = get_logger(level=10)

from dotenv import load_dotenv

load_dotenv()

from pengent.tools.api.search.api_brave_search import ApiBraveSearch


def example():
    api = ApiBraveSearch()
    res = api.search("Brave 検索 API の使い方", limit=5)
    # print(res[0])
    for item in res:
        print(f"Title: {item['title']}")
        print(f"URL: {item['url']}")
        print(f"Description: {item['description']}")
        print("-" * 80)


example()
