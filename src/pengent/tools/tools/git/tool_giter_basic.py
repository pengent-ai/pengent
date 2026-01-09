from typing import Optional, List
from ....tools.tool_utils import tool
from ...api.git.api_gitea import ApiGitea
from ....lib.custom_logger import get_logger

logger = get_logger()


@tool(tags=["git", "coder", "pg"])
def get_git_organizations():
    """
    Gitの組織一覧を取得する関数

    Returns:
        str: 組織名のリスト
    """
    try:
        api = ApiGitea(repo_owner="")
        orgs = api.get_organizations()
        return f"Gittの組織の一覧を取得しました。\n組織数: {len(orgs)}\n" + "\n".join(
            [org["username"] for org in orgs]
        )
    except Exception as e:
        return f"Gitの組織の一覧を取得できませんでした。\nエラー: {str(e)}"


@tool(tags=["git", "coder"])
def get_git_repos(
    owner_name: str,  # オーナー名
):
    """
    Gitリポジトリの一覧を取得する関数

    Parameters:
        owner_name (str): オーナー名(ユーザーまたは組織)

    Returns:
        str: リポジトリ名のリスト
    """
    try:
        api = ApiGitea(repo_owner=owner_name)
        repos = api.get_repos()
        return (
            "GitHubリポジトリの一覧を取得しました。\n"
            f"オーナー: {owner_name}\nリポジトリ数: {len(repos)}\n"
            + "\n".join([repo["name"] for repo in repos])
        )
    except Exception as e:
        return f"GitHubリポジトリの一覧を取得できませんでした。\nエラー: {str(e)}"


@tool(tags=["git", "pg"])
def create_git_branch(
    repo_name: str,  # リポジトリ名
    owner_name: str,  # オーナー名
    branch_name: str,  # ブランチ名
    base_branch: str = "main",  # ベースブランチ名
):
    """
    Gitリポジトリに新しいブランチを作成する関数

    Parameters:
        repo_name (str): リポジトリ名
        owner_name (str): オーナー名
        branch_name (str): 作成するブランチ名
        base_branch (str): ベースブランチ名(デフォルトは"main")

    Returns:
        str: 成功メッセージまたはエラーメッセージ
    """
    try:
        api = ApiGitea(repo_owner=owner_name)
        api.create_branches(
            repo_name=repo_name,
            new_branch_name=branch_name,
            old_ref_name=base_branch,
        )
        return (
            f"GitHubリポジトリ '{owner_name}/{repo_name}' "
            f"に新しいブランチ '{branch_name}' を作成しました。"
        )
    except Exception as e:
        return (
            f"GitHubリポジトリ '{owner_name}/{repo_name}' "
            f"に新しいブランチ '{branch_name}' を作成できませんでした。\n"
            f"エラー: {str(e)}"
        )


@tool(tags=["git", "pg"])
def create_git_repo(
    repo_name: str,  # リポジトリ名
    owner_name: str,  # オーナー名
    description: Optional[str] = "",
    private: Optional[bool] = True,
):
    """
    Gitリポジトリを作成する関数

    Parameters:
        repo_name (str): リポジトリ名
        owner_name (str): オーナー名

        description (str): リポジトリの説明(デフォルトは空文字列)
        private (bool): プライベートリポジトリかどうか(デフォルトはTrue)
    Returns:
        str: 成功メッセージまたはエラーメッセージ
    """
    try:
        api = ApiGitea(repo_owner=owner_name)
        res = api.create_repo(
            repo_name=repo_name,
            org_name=owner_name,
            description=description,
            private=private,
        )
        url = res.get("html_url", "")
        return (
            f"GitHubリポジトリ '{owner_name}/{repo_name}'を作成しました。\nURL: {url}"
        )
    except Exception as e:
        return (
            f"GitHubリポジトリ '{owner_name}/{repo_name}'"
            f"を作成できませんでした。\n"
            f"エラー: {str(e)}"
        )


@tool(tags=["git", "coder", "pg"])
def create_repo_files(
    repo_name: str,
    owner_name: str,
    message: str,
    files: List[dict],  # 各dictに path, content, operation を含む
    branch: Optional[str] = "main",
    new_branch: Optional[str] = None,
):
    """
    Gitリポジトリにファイルを作成または更新する関数

    Parameters:
        repo_name (str): リポジトリ名
        owner_name (str): オーナー名(ユーザーまたは組織)
        message (str): コミットメッセージ
        files (List[dict]): ファイルのリスト
            - path (str): ファイルパス(例: "src/main.py")
            - content (str): ファイル内容(プレーンテキスト)
            - operation (str): "create"、"update"、または "delete"
        branch (str): 対象のブランチ(省略時は "main")
        new_branch (str): 新しく作成するブランチ(省略可)

    Returns:
        str: 成功または失敗のメッセージ
    """
    try:
        logger.debug("tool start create_repo_files.")
        logger.debug(f"repo_name: {repo_name}")
        logger.debug(f"owner_name: {owner_name}")
        logger.debug(f"message: {message}")
        logger.debug(f"branch: {branch}")
        logger.debug(f"new_branch: {new_branch}")
        for file in files:
            logger.debug(f"file.path: {file['path']}")
            logger.debug(f"file.operation: {file['operation']}")
            logger.debug(f"file.content: {file['content'][:20]}")

        api = ApiGitea(repo_owner=owner_name)
        api.create_or_update_contents(
            repo_name=repo_name,
            message=message,
            files=files,
            branch=branch,
            new_branch=new_branch,
        )
        return f"リポジトリ '{owner_name}/{repo_name}' にファイルを反映しました。"
    except Exception as e:
        return (
            f"リポジトリ '{owner_name}/{repo_name}' "
            f"にファイルを反映できませんでした。\n"
            f"エラー: {str(e)}"
        )


@tool(tags=["git", "coder", "pg"])
def get_git_tree(
    repo_name: str,  # リポジトリ名
    owner_name: str,  # オーナー名
    ref: Optional[str] = "main",  # リファレンス(デフォルトは"main")
):
    """
    Gitリポジトリのツリーを取得する関数

    Parameters:
        repo_name (str): リポジトリ名
        owner_name (str): オーナー名
        ref (str): リファレンス(デフォルトは"main")

    Returns:
        str: ツリーの内容
    """
    try:
        api = ApiGitea(repo_owner=owner_name)
        tree_data = api.get_tree(repo_name=repo_name, ref=ref)

        # tree_data は dict なので、tree_data["tree"] にアクセスする必要がある
        return (
            f"GitHubリポジトリ '{owner_name}/{repo_name}' "
            f"のツリーを取得しました。\n"
            + "\n".join(
                [f"{item['path']} ({item['type']})" for item in tree_data["tree"]]
            )
        )
    except Exception as e:
        return (
            f"GitHubリポジトリ '{owner_name}/{repo_name}' "
            f"のツリーを取得できませんでした。\n"
            f"エラー: {str(e)}"
        )


@tool(tags=["git", "coder", "pg"])
def get_git_contents(
    repo_name: str,  # リポジトリ名
    owner_name: str,  # オーナー名
    filepath: str,  # ファイルパス
    ref: Optional[str] = "main",  # リファレンス(デフォルトは"main")
):
    """
    Gitリポジトリの特定のファイルの内容を取得する関数

    Parameters:
        repo_name (str): リポジトリ名
        owner_name (str): オーナー名
        filepath (str): ファイルパス
        ref (str): リファレンス(デフォルトは"main")

    Returns:
        str: ファイルの内容
    """
    try:
        api = ApiGitea(repo_owner=owner_name)
        content = api.get_contents(repo_name=repo_name, filepath=filepath, ref=ref)
        return (
            f"GitHubリポジトリ '{owner_name}/{repo_name}' "
            f"のファイル '{filepath}' の内容を取得しました。\n\n---{content}"
        )
    except Exception as e:
        return (
            f"GitHubリポジトリ '{owner_name}/{repo_name}' "
            f"のファイル '{filepath}' の内容を取得できませんでした。\n"
            f"エラー: {str(e)}"
        )
