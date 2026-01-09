import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
)

from pengent.lib import get_logger

logger = get_logger(level=10)

from dotenv import load_dotenv

load_dotenv()

from pengent.tools.api.search.api_read_webpage import ApiHtmlReader

url = "https://zenn.dev/schroneko/articles/introducing-gpt-5"
print(ApiHtmlReader.get_page(url))
