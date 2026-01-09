import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
)

from pengent.lib import get_logger

logger = get_logger(level=10)

from dotenv import load_dotenv

load_dotenv()

from pengent.tools.api.services.api_hotpepper_gourmet import ApiHotpepperGourmet


def example_gourmet():
    api = ApiHotpepperGourmet()
    res = api.search(
        params={
            "keyword": "焼肉",
            "address": "大阪府羽曳野市",
        }
    )
    logger.debug(res)
    # logger.debug( "\n".join( f"{p['id']} {p['name']}" for p in res))


example_gourmet()
