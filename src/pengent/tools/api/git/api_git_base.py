from abc import ABC, abstractmethod
from typing import List


class ApiGitBase(ABC):
    """
    Git APIのベースクラス

    Notes:
        - GitHub、GitLab、GiteaなどのAPIを統一インターフェースを提供します。
    """

    def __init__(self, repo_owner=None, **kwargs):
        """
        コンストラクタ

        Args:
            **kwargs: APIクライアントに必要なパラメータ
        """
        self.repo_owner = repo_owner

    @classmethod
    @abstractmethod
    def get_repos(cls, owner=None) -> List[str]:
        """
        Gitリポジトリ情報一覧を取得するクラスメソッド
        Args:
            repo_owner (str): リポジトリのオーナー名

        Notes:
            - repo_ownerが指定されていない場合は、全リポジトリ情報を取得する
        """
        raise NotImplementedError("Not implemented: get_repo")

    @abstractmethod
    def get_repo_tree(
        self, repo_name: str, sha: str = None, path_prefix="", tree_recursive=False
    ) -> List[str]:
        """
        Gitリポジトリのファイル及びフォルダ一覧を取得するメソッド

        Args:
            repo_name (str): リポジトリ名
            sha (str): ブランチ名やコミットID(例: main, develop)
            path_prefix (str): 現在のパス(再帰用)
            tree_recursive (bool): Trueなら再帰的に取得する
        """

    def create_repo(
        self,
        repo_name: str,
        description: str = "",
        private: bool = True,
        auto_init: bool = True,
        default_branch: str = "main",
        license: str = "MIT",
        readme: str = "Default",
        **kwargs,
    ) -> dict:
        """
        リポジトリを作成するメソッド

        Args:
            repo_name (str): リポジトリ名
            description (str): 説明文
            private (bool): プライベートリポジトリかどうか
            auto_init (bool): 自動初期化するかどうか
            default_branch (str): デフォルトブランチ名
            license (str): ライセンス名
            readme (str): READMEの種類
        """
        raise NotImplementedError("Not implemented: create_repo")

    # branch-------------------------------

    @abstractmethod
    def get_branches(self, repo_name: str):
        """
        リポジトリのブランチ一覧を取得するメソッド

        Args:
            repo_name (str): リポジトリ名
        """

    @abstractmethod
    def create_branches(
        self, repo_name: str, branch_name: str, old_ref_name: str = None
    ) -> dict:
        """
        リポジトリのブランチを作成するメソッド

        Args:
            repo_name (str): リポジトリ名
            branch_name (str): ブランチ名
            old_ref_name (str): 参照元のブランチ名
        """
        raise NotImplementedError("Not implemented: create_branches")

    @abstractmethod
    def delete_branches(self, repo_name: str, branch_name: str) -> dict:
        """
        リポジトリのブランチを削除するメソッド

        Args:
            repo_name (str): リポジトリ名
            branch_name (str): ブランチ名
        """
        raise NotImplementedError("Not implemented: create_branches")

    # content-------------------------------

    def get_tree(self, repo_name: str, ref: str = None):
        """
        リポジトリのツリー情報を取得するメソッド
        Args:
            repo_name (str): リポジトリ名
            ref (str): 参照するブランチ名、タグ名、またはコミットID
              - (省略時はデフォルトブランチ)
        """
        raise NotImplementedError("Not implemented: get_tree")

    def get_contents(self, repo_name: str, filepath: str, ref: str = None):
        """
        リポジトリ内の特定ファイルやディレクトリの情報を取得するメソッド

        Args:
            repo_name (str): リポジトリ名
            filepath (str): 取得したいファイル or ディレクトリのパス
            ref (str): 参照するブランチ名、タグ名、またはコミットID
              - (省略時はデフォルトブランチ)
        """
        raise NotImplementedError("Not implemented: get_contents")

    def create_or_update_contents(
        self,
        repo_name: str,
        message: str,
        files: List[dict],
        branch="main",
        new_branch=None,
    ):
        """
        リポジトリ内の特定ファイルやディレクトリを作成または更新するメソッド

        Args:
            repo_name (str): リポジトリ名
            files (List[dict]): 作成または更新するファイルの情報
                - path (str): ファイルのパス
                - content (str): ファイルの内容
                - operation (str): "create","update","delete"のいずれか
            branch (str): 参照するブランチ名(省略時はデフォルトブランチ)
        """
        raise NotImplementedError("Not implemented: create_or_update_contents")

    # issus-------------------------------

    def get_issues(
        self,
        repo_name: str,
        state: str = "open",
        labels: List[str] = None,
        q: str = None,
    ):
        """
        イシューを作成するメソッド

        Args:
            repo_name (str): リポジトリ名
            state (str): イシューの状態(open, closed,all)
            labels (List[str]): ラベル名のリスト
            q (str): 検索クエリ(例: "is:open is:issue")
        """
        raise NotImplementedError("Not implemented: create_issues")

    def create_issue(
        self,
        repo_name: str,
        title: str,
        body: str = None,
        labels: List[int] = None,
        assignees: List[str] = None,
        ref: str = None,
    ):
        """
        イシューを作成するメソッド

        Args:
            repo_name (str): リポジトリ名
            title (str): イシューのタイトル
            body (str): イシューの本文
            labels (List[int]): ラベルID
            assignees (List[str]): アサインするユーザー名のリスト
            ref (str): 参照するブランチ名、タグ名、またはコミットID
              - 省略時はデフォルトブランチ
        """
        raise NotImplementedError("Not implemented: create_issues")

    def update_issue(
        self,
        repo_name: str,
        issue_id: int,
        title: str,
        body: str = None,
        state: str = None,
        labels: List[int] = None,
        assignees: List[str] = None,
        ref: str = None,
    ):
        """
        イシューを更新するメソッド(一部更新)

        Args:
            repo_name (str): リポジトリ名
            issue_id (int): イシューID
            title (str): イシューのタイトル
            body (str): イシューの本文
            state (str): イシューの状態(open, closed,all)
            labels (List[int]): ラベルID
            assignees (List[str]): アサインするユーザー名のリスト
            ref (str): 参照するブランチ名、タグ名、またはコミットID
              - 省略時はデフォルトブランチ
        """
        raise NotImplementedError("Not implemented: create_issues")

    def create_issue_commnets(
        self,
        repo_name: str,
        issue_id: int,
        body: str = None,
    ):
        """
        イシューのコメントを作成するメソッド

        Args:
            repo_name (str): リポジトリ名
            issue_id (int): イシューID
            body (str): イシューの本文
        """
        raise NotImplementedError("Not implemented: create_issues")

    def search_issues(self):
        """
        イシューを検索するメソッド

        Args:
        """
        raise NotImplementedError("Not implemented: search_issues")

    # -----------
    # actions secrets

    def get_secrets_org(
        self,
        org_name: str,
        page: int = None,
        limit: int = None,
    ):
        """
        組織のシークレットを取得するメソッド

        Args:
            org_name (str): 組織名
            page (int): ページ番号(省略時は1)
            limit (int): 1ページあたりの取得件数(省略時は100)
        """
        raise NotImplementedError("Not implemented: get_secrets_org")

    def get_secrets_repo(
        self,
        repo_name: str,
        page: int = None,
        limit: int = None,
    ):
        """
        リポジトリのシークレットを取得するメソッド

        Args:
            repo_name (str): リポジトリ名
            page (int): ページ番号(省略時は1)
            limit (int): 1ページあたりの取得件数(省略時は100)
        """
        raise NotImplementedError("Not implemented: get_secrets_repo")

    def create_or_update_secrets_user(self, secretname: str, data: str):
        """
        ユーザーのシークレットを作成または更新するメソッド

        Args:
            secretname (str): シークレット名
            data (str): シークレットのデータ
        """
        raise NotImplementedError("Not implemented: create_or_update_secrets_org")

    def create_or_update_secrets_org(self, org_name: str, secretname: str, data: str):
        """
        組織のシークレットを作成または更新するメソッド

        Args:
            org_name (str): 組織名
            secretname (str): シークレット名
            data (str): シークレットのデータ
        """
        raise NotImplementedError("Not implemented: create_or_update_secrets_org")

    def create_or_update_secrets_repo(self, repo_name: str, secretname: str, data: str):
        """
        リポジトリのシークレットを作成または更新するメソッド

        Args:
            repo_name (str): リポジトリ名
            secretname (str): シークレット名
            data (str): シークレットのデータ

        """
        raise NotImplementedError("Not implemented: create_or_update_secrets_repo")

    def delete_secrets_org(self, org_name: str, secretname: str):
        """
        リポジトリのシークレットを削除するメソッド

        Args:
            org_name (str): 組織名
            secretname (str): シークレット名
        """
        raise NotImplementedError("Not implemented: delete_secrets_repo")

    def delete_secrets_repo(self, repo_name: str, secretname: str):
        """
        リポジトリのシークレットを削除するメソッド

        Args:
            repo_name (str): リポジトリ名
            secretname (str): シークレット名
        """
        raise NotImplementedError("Not implemented: delete_secrets_repo")

    # webhook-------

    def get_webhooks(
        self,
        repo_name: str,
        page: int = None,
        limit: int = None,
    ):
        """
        リポジトリのWebhookを取得するメソッド

        Args:
            repo_name (str): リポジトリ名
            page (int): ページ番号(省略時は1)
            limit (int): 1ページあたりの取得件数(省略時は100)
        """
        raise NotImplementedError("Not implemented: get_webhook")

    def create_webhooks(
        self,
        repo_name: str,
        url: str,
        events: List[str],
        contnt_type: str = "json",
        type: str = "gitea",
        config_option: dict = None,
        authorization_header: str = None,
        active: bool = True,
    ):
        """
        リポジトリのWebhookを登録するメソッド
        Args:
            repo_name (str): リポジトリ名
            url (str): WebhookのURL
            events (List[str]): イベントのリスト(例: ["push", "pull_request","issues"])
            contnt_type (str): コンテンツタイプ(例: "json")
            type (str): Webhookのタイプ(例: "gitea")
                - dingtalk, discord, gitea, gogs, msteams, slack,
                  telegram, feishu, wechatwork, packagist
            config_option (dict): Webhookの設定オプション(secretなど HMAC SHA256)
                - secret (str): Webhookで任意のシークレットで署名(/例: "my_secret")
            authorization_header (str): WebhookのAuthorizationヘッダー
                - example: "Bearer my_token"
            active (bool): Webhookを有効にするかどうか(省略時はTrue)
        """
        raise NotImplementedError("Not implemented: create_webhooks")

    def update_webhooks(
        self,
        repo_name: str,
        webhook_id: int,
        events: List[str] = None,
        contnt_type: str = None,
        type: str = None,
        config: dict = None,
        authorization_header: str = None,
        active: bool = None,
    ):
        """
        リポジトリのWebhookを更新するメソッド(一部)
        Args:
            repo_name (str): リポジトリ名
            events (List[str]): イベントのリスト(例: ["push", "pull_request","issues"])
            type (str): Webhookのタイプ(例: "gitea")
                - dingtalk, discord, gitea, gogs, msteams, slack,
                  telegram, feishu, wechatwork, packagist
            config (dict): urlやcontents_typeなどを修正する場合
            authorization_header (str): WebhookのAuthorizationヘッダー
            active (bool): Webhookを有効にするかどうか(省略時はTrue)
        """
        raise NotImplementedError("Not implemented: update_webhooks")

    def delete_webhooks(self, repo_name: str, webhook_id: int):
        """
        リポジトリのWebhookを削除するメソッド

        Args:
            repo_name (str): リポジトリ名
            webhook_id (int): WebhookのID
        """
        raise NotImplementedError("Not implemented: delete_webhooks")

    def test_webhooks(self, repo_name: str, webhook_id: int, ref: str = None):
        """
        リポジトリのWebhookをテストするメソッド

        Args:
            repo_name (str): リポジトリ名
            webhook_id (int): WebhookのID
            ref (str): 参照するブランチ名、タグ名、またはコミットID
              - 省略時はデフォルトブランチ) クエリパラメータ
        """
        raise NotImplementedError("Not implemented: delete_webhooks")
