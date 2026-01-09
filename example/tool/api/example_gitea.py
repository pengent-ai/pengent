import sys
import os
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..","..","..", "src")))

from pengent.lib import get_logger
logger=get_logger(level=10)

from dotenv import load_dotenv
load_dotenv()

from pengent.tools.api.git.api_gitea import ApiGitea


def example_create_or_update_contents():
    api = ApiGitea(repo_owner="ai-program")
    res = api.create_or_update_contents(
        repo_name="ai-pengent-workspace",
        message="updx dockerfile",
        branch="main",
        new_branch="develop",
        files=[
            {
                "path": "src/main.py",
                "operation": "create",
                "content": """\
import requests

def main():
    print("Hello, this is a Python 3.12 test container.")

    # シンプルなHTTP GETリクエストで動作確認
    try:
        response = requests.get("https://httpbin.org/get")
        if response.status_code == 200:
            print("HTTP request successful.")
            print("Response JSON:", response.json())
        else:
            print(f"HTTP request failed: {response.status_code}")
    except Exception as e:
        print(f"Exception during HTTP request: {e}")

if __name__ == "__main__":
    main()
"""
            }
        ],
    )
    logger.debug(res)

def example_git_tree():
    api = ApiGitea(repo_owner="ai-program")
    api.get_tree(
        repo_name="ai-pengent-workspace",
        ref="main",
    )

def example_git_contents():
    api = ApiGitea(repo_owner="ai-program")
    res = api.get_contents(
        repo_name="ai-pengent-workspace",
        filepath="Dockerfile",
        ref="main",
    )
    logger.debug(res)

def example_get_organizations():
    api = ApiGitea(repo_owner="ai-program")
    res = api.get_organizations()
    logger.debug(res)

def example_create_or_update_contents_from_file():
    api = ApiGitea(repo_owner="ai-program")
    # ファイルのパスを指定
    file_path = "output.txt"
    # ファイルの内容を読み込む
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()
    res = api.create_or_update_contents(
        repo_name="penframe",
        message="アプリの概要を追加",
        branch="main",
        new_branch="develop",
        files=[
            {
                "path": "src/main.py",
                "operation": "create",
                "content": file_content
            }
        ]
    )
    logger.debug(res)

def example_seacrets():
    api = ApiGitea(repo_owner="ai-program")
    # res = api.get_secrets_repo(
    #     repo_name="pengent",
    # )
    # logger.debug(res)
    api.create_or_update_secrets_repo(
        repo_name="pengent",
        secretname="GEMINI_API_KEY",
        data="XXXXXXXXXXXXXXX",
    )

def example_pulls():
    api = ApiGitea(repo_owner="ai-program")
    api.create_pull_requests(
        repo_name="pengent",
        title="Gitアクション及びツールの修正",
        body="修正",
        head="develop",
        base="main",
    )

def example_tags():
    ApiGitea(repo_owner="ai-program")
    # res = api.get_tags(
    #     repo_name="pengent",
    # )
    # logger.debug(res)
    # res = api.delete_tag(
    #     repo_name="pengent",
    #     tag_name="1.0.0-dev",
    # )
    # logger.debug(res)

# example_get_organizations()
# example_git_tree()
# example_git_contents()
# example_create_or_update_contents()
# example_create_or_update_contents_from_file()
# example_seacrets()
# example_pulls()
example_tags()
