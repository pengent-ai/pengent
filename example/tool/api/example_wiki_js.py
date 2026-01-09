import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
)

from pengent.lib import get_logger

logger = get_logger(level=10)

from dotenv import load_dotenv

load_dotenv()


from pengent.tools.api.post.api_wiki_js import ApiWikiJS


def example_seach():
    api = ApiWikiJS()
    res = api.search("Python")
    logger.debug(res)


def example_show():
    api = ApiWikiJS()
    res = api.show(174)
    logger.debug(res)


# example_seach()
example_show()
