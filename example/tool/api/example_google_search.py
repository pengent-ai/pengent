import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
)

from pengent.lib import get_logger

logger = get_logger(level=10)

from dotenv import load_dotenv

load_dotenv()

from pengent.tools.api.search.api_google_web_search import ApiGoogleWebSearch


def example():
    api = ApiGoogleWebSearch()
    res = api.search("Google ADK")
    logger.debug(res)


example()
