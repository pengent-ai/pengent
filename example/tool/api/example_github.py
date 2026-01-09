import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
)

from pengent.lib import get_logger

logger = get_logger(level=10)

from dotenv import load_dotenv

load_dotenv()

from pengent.tools.api.git.api_github import ApiGithub


def example_search_repo():
    api = ApiGithub()
    res = api.search_repo(
        query="lowcode app stars:>1000", sorting="stars", page=1, per_page=10
    )
    # sort=stars language:python
    # stars:>1000   スター1000以上
    # language:Python   Python言語
    # created:>2024-01-01   2024年以降に作成されたもの
    # topic:llm GitHubのtopicが llm のもの
    # is:fork false フォークでないオリジナルリポジトリ
    for repo in res:
        logger.info(
            f"Repository Name: {repo['name']}, URL: {repo['html_url']} "
            f"stars: {repo['stargazers_count']}"
        )


def example_search_code():
    api = ApiGithub()
    res = api.search_code(
        query="import requests", language="python", page=1, per_page=10
    )
    for code in res:
        logger.info(
            f"File Name: {code['name']}, URL: {code['html_url']} in Repository: "
            f"{code['repository']['full_name']}"
        )


# example_search_repo()
example_search_code()
