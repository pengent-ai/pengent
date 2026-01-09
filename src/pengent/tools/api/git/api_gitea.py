import os
import requests
from ....lib.custom_logger import get_logger
from .api_git_base import ApiGitBase
import base64
from typing import List

logger = get_logger()


class ApiGitea(ApiGitBase):
    """
    GiteaAPIのベースクラス

    Notes:
        - Gitea API Docs: https://docs.gitea.com/api/1.23/
    """

    _API_URL = os.getenv("GITEA_API_URL")
    _API_KEY = os.getenv("GITEA_API_KEY")
    _HEADERS = {
        "Authorization": f"token {_API_KEY}",
        "Content-Type": "application/json",
    }

    @classmethod
    def get_organizations(cls):
        """
        Giteaの組織情報一覧を取得するクラスメソッド
        Returns:
            list: 組織情報のリスト
        """
        logger.info("Get Gitea organizations")
        uri = "/api/v1/user/orgs"
        # GETリクエストを送信
        response = requests.get(f"{cls._API_URL}{uri}", headers=cls._HEADERS)
        response.raise_for_status()
        json_data = response.json()
        logger.info(f"get to Gitea success: {response.status_code}")
        logger.debug(f"response: {json_data}")
        return json_data

    @classmethod
    def get_repos(cls, repo_owner=None):
        """
        Giteaのリポジトリ情報一覧を取得するクラスメソッド
        Args:
            repo_name (str): リポジトリ名

        """
        logger.info(f"Get Gitea repositorys: {repo_owner}")
        if repo_owner:
            uri = f"/api/v1/users/{repo_owner}/repos"
        else:
            uri = "/api/v1/user/repos"

        # GETリクエストを送信
        response = requests.get(f"{cls._API_URL}{uri}", headers=cls._HEADERS)
        response.raise_for_status()
        json_data = response.json()
        full_names = [repo["full_name"] for repo in json_data]

        logger.info(f"get to Gitea success: {full_names}")
        return json_data

    def get_repo_tree(self, repo_name: str, sha):
        logger.info(f"Get Gitea repositorys: {repo_name}")
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/git/trees/{sha}"

        # GETリクエストを送信
        response = requests.get(f"{self._API_URL}{uri}", headers=self._HEADERS)
        response.raise_for_status()
        json_data = response.json()

        logger.info(f"get to Gitea success: {json_data}")
        return json_data

    def get_branches(self, repo_name: str):
        logger.info(f"Get Gitea branches: {repo_name}")
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/branches"
        # GETリクエストを送信
        response = requests.get(f"{self._API_URL}{uri}", headers=self._HEADERS)
        response.raise_for_status()
        json_data = response.json()
        logger.info(f"get to Gitea success: {json_data}")
        return json_data

    def create_repo(
        self,
        repo_name: str,
        org_name: str = None,
        description: str = "",
        private: bool = True,
        auto_init: bool = True,
        default_branch: str = "main",
        license: str = "MIT",
        readme: str = "Default",
        **kwargs,
    ) -> dict:
        logger.info(f"Create Gitea repo: {repo_name}")
        if org_name:
            uri = f"/api/v1/orgs/{org_name}/repos"
        else:
            uri = "/api/v1/user/repos"

        post_data = {
            "name": repo_name,
            "description": description,
            "private": private,
            "auto_init": auto_init,
            "default_branch": default_branch,
            "license": license,
            "readme": readme,
        }

        # kwargsで追加オプションを受け取る(例：gitignores, template, etc.)
        post_data.update(kwargs)

        response = requests.post(
            f"{self._API_URL}{uri}", json=post_data, headers=self._HEADERS
        )
        response.raise_for_status()
        json_data = response.json()
        logger.info(f"Repo created successfully: {json_data}")
        return json_data

    def create_branches(
        self, repo_name: str, new_branch_name: str, old_ref_name: str = None
    ) -> dict:
        logger.info(f"Get Gitea branches: {repo_name}")
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/branches"
        # POSTリクエストを送信
        post = {
            "new_branch_name": new_branch_name,
            "old_ref_name": old_ref_name,
        }
        response = requests.post(
            f"{self._API_URL}{uri}", json=post, headers=self._HEADERS
        )
        response.raise_for_status()
        json_data = response.json()
        logger.info(f"get to Gitea success: {json_data}")
        return json_data

    def get_tree(
        self,
        repo_name: str,
        ref: str = "main",
    ):
        logger.info(f"Get Gitea tree: {repo_name}")
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/git/refs/heads/{ref}"
        # GETリクエストを送信
        response = requests.get(f"{self._API_URL}{uri}", headers=self._HEADERS)
        response.raise_for_status()
        json_data = response.json()
        commit_sha = json_data[0].get("object", {}).get("sha")
        logger.debug(f"get to Gitea success: {commit_sha}")
        # shaを取得してツリー情報(tree.sha)を取得
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/git/commits/{commit_sha}"
        response = requests.get(f"{self._API_URL}{uri}", headers=self._HEADERS)
        response.raise_for_status()
        json_data = response.json()
        tree_sha = json_data["commit"]["tree"]["sha"]
        logger.debug(f"get to Gitea commit tree success.{tree_sha}")
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/git/trees/{tree_sha}"
        uri += "?recursive=1"
        # ツリー情報を取得
        response = requests.get(f"{self._API_URL}{uri}", headers=self._HEADERS)
        response.raise_for_status()
        json_data = response.json()
        logger.info(f"get to Gitea tree success: {json_data}")
        return json_data

    def get_contents(self, repo_name: str, filepath: str, ref: str = None):
        logger.info(f"Get Gitea contents: {repo_name}")
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/contents/{filepath}"
        # GETリクエストを送信
        params = {
            key: value
            for key, value in {
                "ref": ref,
            }.items()
            if value is not None
        }
        response = requests.get(
            f"{self._API_URL}{uri}", params=params, headers=self._HEADERS
        )
        response.raise_for_status()
        json_data = response.json()
        logger.info(f"get to Gitea success: {json_data}")
        # base64デコード
        if "content" in json_data:
            json_data["content"] = base64.b64decode(json_data["content"]).decode()
        return json_data

    def create_or_update_contents(
        self,
        repo_name: str,
        message: str,
        files: List[dict],
        branch="main",
        new_branch=None,
    ):
        logger.info(f"Get Gitea create_or_update_contents: {repo_name}")
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/contents"

        # filesの形式を確認
        for file in files:
            # base64エンコード
            file["content"] = base64.b64encode(file["content"].encode()).decode()

        # POSTリクエストを送信
        post = {
            "message": message,
            "files": files,
            "branch": branch,
            "new_branch": new_branch,
        }
        response = requests.post(
            f"{self._API_URL}{uri}", json=post, headers=self._HEADERS
        )
        response.raise_for_status()
        json_data = response.json()
        logger.info(f"get to Gitea success: {json_data}")
        return json_data

    # issus-------------------------------

    def get_issues(
        self,
        repo_name: str,
        state: str = "open",
        labels: List[str] = None,
        q: str = None,
    ):
        logger.info(f"Get Gitea issues: {repo_name}")
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/issues"
        # GETリクエストを送信
        params = {}
        if state:
            params["state"] = state
        if labels:
            params["labels"] = ",".join(labels)
        if q:
            params["q"] = q

        response = requests.get(
            f"{self._API_URL}{uri}", params=params, headers=self._HEADERS
        )
        response.raise_for_status()
        json_data = response.json()
        logger.info(f"get to Gitea success: {json_data}")
        return json_data

    def create_issue(
        self,
        repo_name: str,
        title: str,
        body: str = None,
        labels: List[int] = None,
        assignees: List[str] = None,
        ref: str = None,
    ):
        logger.info(f"Create Gitea issues: {repo_name}")
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/issues"
        # POSTリクエストを送信
        post = {
            "title": title,
            "body": body,
        }

        if labels:
            post["labels"] = labels
        if assignees:
            post["assignees"] = assignees
        if ref:
            post["ref"] = ref

        response = requests.post(
            f"{self._API_URL}{uri}", json=post, headers=self._HEADERS
        )
        response.raise_for_status()
        json_data = response.json()
        logger.info(
            f"get to Gitea success id:{json_data['id']}:{json_data['html_url']}"
        )
        logger.debug(f"response: {json_data}")
        return json_data

    def update_issue(
        self,
        repo_name: str,
        issue_id: int,
        title: str = None,
        body: str = None,
        state: str = None,
        labels: List[int] = None,
        assignees: List[str] = None,
        ref: str = None,
    ):
        logger.info(f"Update(patch) Gitea issues: {repo_name}")
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/issues/{issue_id}"
        # PATCHリクエストを送信
        post = {
            key: value
            for key, value in {
                "title": title,
                "body": body,
                "state": state,
                "labels": labels,
                "assignees": assignees,
                "ref": ref,
            }.items()
            if value is not None
        }
        response = requests.patch(
            f"{self._API_URL}{uri}", json=post, headers=self._HEADERS
        )
        response.raise_for_status()
        json_data = response.json()
        logger.info(
            f"patch to Gitea success id:{json_data['id']}:{json_data['html_url']}"
        )
        logger.debug(f"response: {json_data}")
        return json_data

    def create_issue_commnets(
        self,
        repo_name: str,
        issue_id: int,
        body: str = None,
    ):
        logger.info(f"Create Gitea issue comments: {repo_name}")
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/issues/{issue_id}/comments"
        # POSTリクエストを送信
        post = {
            "body": body,
        }
        response = requests.post(
            f"{self._API_URL}{uri}", json=post, headers=self._HEADERS
        )
        response.raise_for_status()
        json_data = response.json()
        logger.info(f"Create Gitea issues comments: {repo_name}")
        logger.debug(f"response: {json_data}")
        return json_data

    # -----------
    # secrets (Githubでは対応済み)

    def get_secrets_org(
        self,
        org_name: str,
        page: int = None,
        limit: int = None,
    ):
        logger.info(f"get_secrets_org: {org_name}")
        uri = f"/api/v1/orgs/{org_name}/actions/secrets"
        # GETリクエストを送信

        params = {
            key: value
            for key, value in {
                "page": page,
                "limit": limit,
            }.items()
            if value is not None
        }
        response = requests.get(
            f"{self._API_URL}{uri}", params=params, headers=self._HEADERS
        )
        response.raise_for_status()
        json_data = response.json()
        logger.info(f"get_secrets_org success: {json_data}")
        return json_data

    def get_secrets_repo(
        self,
        repo_name: str,
        page: int = None,
        limit: int = None,
    ):
        logger.info(f"get_secrets_repo: {repo_name}")
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/actions/secrets"
        # GETリクエストを送信
        params = {
            key: value
            for key, value in {
                "page": page,
                "limit": limit,
            }.items()
            if value is not None
        }
        response = requests.get(
            f"{self._API_URL}{uri}", params=params, headers=self._HEADERS
        )
        response.raise_for_status()
        json_data = response.json()
        logger.info(f"get_secrets_repo success: {json_data}")
        return json_data

    def create_or_update_secrets_user(self, secretname: str, data: str):
        logger.info("create_or_update_secrets_user.")
        uri = f"/api/v1/user/actions/secrets/{secretname}"
        # PUTリクエストを送信
        post = {
            "data": data,
        }
        response = requests.put(
            f"{self._API_URL}{uri}", json=post, headers=self._HEADERS
        )
        response.raise_for_status()
        logger.info(f"create_or_update_secrets_success: {response.status_code}")
        return True

    def create_or_update_secrets_repo(self, repo_name: str, secretname: str, data: str):
        logger.info(f"create_or_update_secrets_repo: {repo_name}")
        uri = (
            f"/api/v1/repos/{self.repo_owner}/{repo_name}/actions/secrets/{secretname}"
        )
        # PUTリクエストを送信
        post = {
            "data": data,
        }
        response = requests.put(
            f"{self._API_URL}{uri}", json=post, headers=self._HEADERS
        )
        response.raise_for_status()
        logger.info(f"create_or_update_secrets_repo success: {response.status_code}")
        return True

    def delete_secrets_repo(
        self,
        repo_name: str,
        secretname: str,
    ):
        logger.info(f"delete_secrets_repo: {repo_name}")
        uri = (
            f"/api/v1/repos/{self.repo_owner}/{repo_name}/actions/secrets/{secretname}"
        )
        # DELETEリクエストを送信
        response = requests.delete(f"{self._API_URL}{uri}", headers=self._HEADERS)
        response.raise_for_status()
        logger.info(f"delete_secrets_repo success: {response.status_code}")
        return True

    def delete_secrets_user(
        self,
        secretname: str,
    ):
        logger.info("delete_secrets_user.")
        uri = f"/api/v1/user/actions/secrets/{secretname}"
        # DELETEリクエストを送信
        response = requests.delete(f"{self._API_URL}{uri}", headers=self._HEADERS)
        response.raise_for_status()
        logger.info(f"delete_secrets_user success: {response.status_code}")
        return True

    # webhook-------

    def get_webhooks(
        self,
        repo_name: str,
        page: int = None,
        limit: int = None,
    ):
        logger.info(f"get_webhooks: {repo_name}")
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/hooks"
        # GETリクエストを送信
        params = {
            key: value
            for key, value in {
                "page": page,
                "limit": limit,
            }.items()
            if value is not None
        }
        response = requests.get(
            f"{self._API_URL}{uri}", params=params, headers=self._HEADERS
        )
        response.raise_for_status()
        json_data = response.json()
        logger.info(f"get_webhooks success: {json_data}")
        return json_data

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
        logger.info(f"create_webhooks: {repo_name}")
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/hooks"

        # config の基本構成
        config = {
            "url": url,
            "content_type": contnt_type,
        }
        # オプションがあればマージ
        if config_option:
            config.update(config_option)
        # POSTリクエストを送信
        post = {"active": active, "events": events, "type": type, "config": config}
        if authorization_header:
            post["authorization_header"] = authorization_header

        response = requests.post(
            f"{self._API_URL}{uri}", json=post, headers=self._HEADERS
        )
        response.raise_for_status()
        json_data = response.json()
        logger.info(f"create_webhooks success: {json_data}")
        return json_data

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
        logger.info(f"update_webhooks: {repo_name}")
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/hooks/{webhook_id}"
        # PATCHリクエストを送信
        post = {
            key: value
            for key, value in {
                "events": events,
                "content_type": contnt_type,
                "type": type,
                "config": config,
                "authorization_header": authorization_header,
                "active": active,
            }.items()
            if value is not None
        }
        response = requests.patch(
            f"{self._API_URL}{uri}", json=post, headers=self._HEADERS
        )
        response.raise_for_status()
        json_data = response.json()
        logger.info(f"update_webhooks success: {json_data}")
        logger.debug(f"response: {json_data}")
        return json_data

    def delete_webhooks(self, repo_name: str, webhook_id: int):
        logger.info(f"delete_webhooks: {repo_name}")
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/hooks/{webhook_id}"
        # DELETEリクエストを送信
        response = requests.delete(f"{self._API_URL}{uri}", headers=self._HEADERS)
        response.raise_for_status()
        logger.info(f"delete_webhooks success: {response.status_code}")
        return True

    def test_webhooks(self, repo_name: str, webhook_id: int, ref: str = None):
        logger.info(f"test_webhooks: {repo_name}")
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/hooks/{webhook_id}/testa"
        # POSTリクエストを送信
        params = {
            key: value
            for key, value in {
                "ref": ref,
            }.items()
            if value is not None
        }
        response = requests.post(
            f"{self._API_URL}{uri}", params=params, headers=self._HEADERS
        )
        response.raise_for_status()
        logger.info(f"delete_webhooks success: {response.status_code}")
        return True

    # ---------------------
    # tags
    def get_tags(
        self,
        repo_name: str,
        page: int = None,
        limit: int = None,
    ):
        logger.info(f"get_tags: {repo_name}")
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/tags"
        # GETリクエストを送信
        params = {
            key: value
            for key, value in {
                "page": page,
                "limit": limit,
            }.items()
            if value is not None
        }
        response = requests.get(
            f"{self._API_URL}{uri}", params=params, headers=self._HEADERS
        )
        response.raise_for_status()
        json_data = response.json()
        logger.info(f"get_tags success: {json_data}")
        return json_data

    def create_tag(
        self, repo_name: str, tag_name: str, message: str = None, target: str = None
    ):
        logger.info(f"create_tag: {repo_name}")
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/tags"
        # POSTリクエストを送信
        post = {
            "tag_name": tag_name,
            "target": target,  # タグの対象コミットSHA
            "message": message,  # タグ名
        }
        response = requests.post(
            f"{self._API_URL}{uri}", json=post, headers=self._HEADERS
        )
        response.raise_for_status()
        json_data = response.json()
        logger.info(f"create_tag success: {json_data}")
        return json_data

    def delete_tag(self, repo_name: str, tag_name: str):
        logger.info(f"delete_tag: {repo_name}")
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/tags/{tag_name}"
        # DELETEリクエストを送信
        response = requests.delete(f"{self._API_URL}{uri}", headers=self._HEADERS)
        response.raise_for_status()
        logger.info(f"delete_tag success: {response.status_code}")
        return True

    # ---------------------
    # プルリクエスト(pull)

    def create_pull_requests(
        self,
        repo_name: str,
        title: str,
        head: str,
        base: str = "develop",
        body: str = None,
    ):
        logger.info(f"create_pull_requests: {repo_name}")
        uri = f"/api/v1/repos/{self.repo_owner}/{repo_name}/pulls"
        # POSTリクエストを送信
        post = {
            "title": title,
            "head": head,
            "base": base,
            "body": body,
        }
        response = requests.post(
            f"{self._API_URL}{uri}", json=post, headers=self._HEADERS
        )
        response.raise_for_status()
        json_data = response.json()
        logger.debug(f"create_pull_requests success: {json_data}")
        return json_data
