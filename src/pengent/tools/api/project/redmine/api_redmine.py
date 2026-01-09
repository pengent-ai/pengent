import requests
import os
from .....lib.custom_logger import get_logger

logger = get_logger()


class ApiRedmine:
    """
    Redmine APIクライアント
    """
    BASE_URL = os.getenv("REDMINE_API_URL")  # 例: "https://redmine.example.com"
    API_KEY = os.getenv("REDMINE_API_KEY")  # RedmineのAPIキー

    @classmethod
    def _headers(cls):
        return {"X-Redmine-API-Key": cls.API_KEY, "Content-Type": "application/json"}

    # --------------------------------------------
    @classmethod
    def get_users(cls, limit=100):
        """
        Redmineのユーザー一覧を取得(有効ユーザー)

        Returns:
            list: ユーザー情報のリスト
        """
        url = f"{cls.BASE_URL}/users.json?status=1&limit={limit}"
        response = requests.get(url, headers=cls._headers())
        response.raise_for_status()
        json_data = response.json()
        return json_data.get("users", [])

    @classmethod
    def create_user(
        cls,
        login: str,
        firstname: str,
        lastname: str,
        mail: str,
        password: str,
        must_change_passwd: bool = True,
        status: int = 1,
    ):
        """
        新しいRedmineユーザーを作成する

        Args:
            login (str): ログインID
            firstname (str): 名
            lastname (str): 姓
            mail (str): メールアドレス
            password (str): パスワード
            must_change_passwd (bool): 初回ログイン時にパスワード変更必須
            status (int): ステータス(1 = 有効, 3 = 登録待ち)

        Returns:
            dict: 作成されたユーザー情報
        """
        url = f"{cls.BASE_URL}/users.json"
        payload = {
            "user": {
                "login": login,
                "firstname": firstname,
                "lastname": lastname,
                "mail": mail,
                "password": password,
                "must_change_passwd": must_change_passwd,
                "status": status,
            }
        }

        logger.info(f"Creating user: {login}")
        response = requests.post(url, json=payload, headers=cls._headers())
        response.raise_for_status()
        json_data = response.json()
        return json_data.get("user")

    @classmethod
    def delete_user(cls, user_id: int):
        """
        Redmineユーザーを削除する

        Args:
            user_id (int): 削除対象ユーザーのID

        Returns:
            str: 結果メッセージ
        """
        url = f"{cls.BASE_URL}/users/{user_id}.json"

        logger.info(f"Deleting user: {user_id}")
        response = requests.delete(url, headers=cls._headers())
        response.raise_for_status()
        return True

    # --------------------------------------------
    @classmethod
    def get_roles(cls):
        """
        ロール一覧を取得

        Returns:
            list: ロールのリスト(id, name など)
        """
        url = f"{cls.BASE_URL}/roles.json"
        response = requests.get(url, headers=cls._headers())
        response.raise_for_status()
        json_data = response.json()
        return json_data.get("roles", [])

    # --------------------------------------------
    @classmethod
    def get_projects(cls):
        """
        Redmineのプロジェクト一覧を取得する

        Returns:
            list: プロジェクトのリスト(id, name, identifier, description など)
        """
        url = f"{cls.BASE_URL}/projects.json?limit=100"
        logger.info(f"Fetching Redmine projects: {url}")

        response = requests.get(url, headers=cls._headers())

        if response.status_code == 200:
            data = response.json()
            return data.get("projects", [])
        else:
            raise Exception(
                f"Failed to fetch projects: {response.status_code} - {response.text}"
            )

    @classmethod
    def create_project(
        cls,
        name: str,
        identifier: str,
        description: str = "",
        is_public: bool = True,
        parent_id: int = None,
    ):
        """
        Redmineで新しいプロジェクトを作成する

        Args:
            name (str): プロジェクト名(表示名)
            identifier (str): 識別子(URLに使われる短縮名)
            description (str): 説明文
            is_public (bool): 公開フラグ(デフォルト: True)
            parent_id (int): 親プロジェクトID(階層構造用、任意)

        Returns:
            dict: 作成されたプロジェクト情報
        """
        url = f"{cls.BASE_URL}/projects.json"
        payload = {
            "project": {
                "name": name,
                "identifier": identifier,
                "description": description,
                "is_public": is_public,
            }
        }
        if parent_id:
            payload["project"]["parent_id"] = parent_id

        logger.info(f"Creating project: {identifier}")
        response = requests.post(url, json=payload, headers=cls._headers())

        if response.status_code == 201:
            return response.json()["project"]
        else:
            raise Exception(
                f"Failed to create project: {response.status_code} - {response.text}"
            )

    @classmethod
    def delete_project(cls, identifier: str):
        """
        Redmineのプロジェクトを削除する

        Args:
            identifier (str): プロジェクト識別子

        Returns:
            str: 削除完了メッセージ
        """
        url = f"{cls.BASE_URL}/projects/{identifier}.json"

        logger.info(f"Deleting project: {identifier}")
        response = requests.delete(url, headers=cls._headers())
        response.raise_for_status()
        return True

    @classmethod
    def get_project_members(cls, project_identifier: str):
        """
        プロジェクトのメンバー一覧を取得

        Returns:
            list: メンバー情報
        """
        url = f"{cls.BASE_URL}/projects/{project_identifier}/memberships.json"
        response = requests.get(url, headers=cls._headers())
        logger.info(f"get project members: {project_identifier}")
        response.raise_for_status()
        json_data = response.json()
        logger.debug(f"json_data: {json_data}")
        return json_data.get("memberships", [])

    @classmethod
    def create_project_member(
        cls, project_identifier: str, user_id: int, role_ids: list[int]
    ):
        """
        プロジェクトにユーザーを追加

        Args:
            user_id (int): ユーザーID
            role_ids (list[int]): 付与するロールID(例: [3])

        Returns:
            dict: 作成されたメンバー情報
        """
        url = f"{cls.BASE_URL}/projects/{project_identifier}/memberships.json"
        payload = {"membership": {"user_id": user_id, "role_ids": role_ids}}
        logger.info(
            f"Creating project member: {project_identifier}, "
            f"user_id: {user_id}, role_ids: {role_ids}"
        )
        response = requests.post(url, headers=cls._headers(), json=payload)
        response.raise_for_status()
        json_data = response.json()
        logger.debug(f"json_data: {json_data}")

    @classmethod
    def delete_member(cls, membership_id: int):
        """
        メンバーシップIDを指定して削除

        Args:
            membership_id (int): メンバーシップID

        Returns:
            bool: 削除結果
        """
        url = f"{cls.BASE_URL}/memberships/{membership_id}.json"

        logger.info(f"Deleting membership: {membership_id}")
        response = requests.delete(url, headers=cls._headers())
        response.raise_for_status()
        return True

    # --------------------------------------------

    @classmethod
    def get_issues(
        cls,
        project_identifier: str = None,
        status_id: int = None,
        assigned_to_id: int = None,
        limit: int = 100,
    ):
        """
        チケット一覧を取得

        Args:
            project_identifier (str): プロジェクト識別子(任意)
            status_id (int): ステータスID(任意)
            assigned_to_id (int): 担当者ユーザーID(任意)
            limit (int): 最大件数

        Returns:
            list: チケットリスト
        """
        params = {"limit": limit}
        if status_id is not None:
            params["status_id"] = status_id
        if assigned_to_id is not None:
            params["assigned_to_id"] = assigned_to_id

        if project_identifier:
            url = f"{cls.BASE_URL}/projects/{project_identifier}/issues.json"
        else:
            url = f"{cls.BASE_URL}/issues.json"
        response = requests.get(url, headers=cls._headers(), params=params)
        response.raise_for_status()
        json_data = response.json()
        logger.debug(f"json_data: {json_data}")
        return json_data.get("issues", [])

    @classmethod
    def show_issue(cls, issue_id: int):
        """
        チケットを1件取得

        Returns:
            dict: チケット詳細
        """
        url = f"{cls.BASE_URL}/issues/{issue_id}.json"
        response = requests.get(url, headers=cls._headers())
        response.raise_for_status()
        json_data = response.json()
        return json_data.get("issue")

    @classmethod
    def create_issue(
        cls,
        project_identifier: str,
        subject: str,
        description: str = "",
        assigned_to_id: int = None,
        tracker_id: int = 1,
        priority_id: int = 2,
        parent_issue_id: int = None,
        due_date: str = None,
        done_ratio: int = None,
    ):
        """
        新しいチケットを作成

        Args:
            project_identifier (str): プロジェクト識別子
            subject (str): チケット件名
            description (str): 説明
            assigned_to_id (int): 担当者ユーザーID(任意)
            tracker_id (int): トラッカーID(1: バグ, 2: 機能, 3: サポート)
            priority_id (int): 優先度(2: 通常, 3: 高, 4: 緊急)
            parent_issue_id (int): 親チケットID(任意)
            due_date (str): 期限日(YYYY-MM-DD)(任意 ISO形式)
            done_ratio (int): 完了率(0-100)(任意)

        Returns:
            dict: 作成されたチケット情報
        """
        url = f"{cls.BASE_URL}/issues.json"
        payload = {
            "issue": {
                "project_id": project_identifier,
                "subject": subject,
                "description": description,
                "tracker_id": tracker_id,
                "priority_id": priority_id,
            }
        }
        if assigned_to_id:
            payload["issue"]["assigned_to_id"] = assigned_to_id
        if parent_issue_id:
            payload["issue"]["parent_issue_id"] = parent_issue_id
        if due_date:
            payload["issue"]["due_date"] = due_date
        if done_ratio is not None:
            payload["issue"]["done_ratio"] = done_ratio

        logger.info(f"Creating issue: {subject}, project: {project_identifier}")
        response = requests.post(url, headers=cls._headers(), json=payload)
        response.raise_for_status()
        json_data = response.json()
        logger.debug(f"json_data: {json_data}")
        return json_data.get("issue")

    @classmethod
    def update_issue(
        cls,
        issue_id: int,
        subject: str = None,
        description: str = None,
        status_id: int = None,
        assigned_to_id: int = None,
        notes: str = None,
        done_ratio=None,
        due_date=None,
    ):
        """
        チケットの更新(件名、説明、ステータス)

        Args:
            issue_id (int): チケットID
            subject (str): 件名(任意)
            description (str): 説明(任意)
            status_id (int): ステータスID(任意)
            assigned_to_id (int): 担当者ユーザーID(任意)
            notes (str): コメント(任意)
            done_ratio (int): 完了率(0-100)(任意)
            due_date (str): 期限日(YYYY-MM-DD)(任意 ISO形式)

        Returns:
            str: 更新完了メッセージ
        """
        url = f"{cls.BASE_URL}/issues/{issue_id}.json"
        issue_data = {}
        if subject:
            issue_data["subject"] = subject
        if description:
            issue_data["description"] = description
        if status_id:
            issue_data["status_id"] = status_id
        if assigned_to_id:
            issue_data["assigned_to_id"] = assigned_to_id
        if notes:
            issue_data["notes"] = notes
        if done_ratio is not None:
            issue_data["done_ratio"] = done_ratio
        if due_date:
            issue_data["due_date"] = due_date  # "YYYY-MM-DD"
        payload = {"issue": issue_data}
        response = requests.put(url, headers=cls._headers(), json=payload)
        response.raise_for_status()
        json_data = response.json()
        logger.debug(f"json_data: {json_data}")
        return json_data

    @classmethod
    def delete_issue(cls, issue_id: int):
        """
        チケットの削除

        Args:
            issue_id (int): チケットID

        Returns:
            str: 削除結果
        """
        url = f"{cls.BASE_URL}/issues/{issue_id}.json"
        response = requests.delete(url, headers=cls._headers())
        response.raise_for_status()
        logger.info(f"Deleting issue: {issue_id}")
        return True

    @classmethod
    def get_issue_statuses(cls):
        """
        チケットステータス一覧を取得

        Returns:
            list: ステータスリスト (各要素は {"id": int, "name": str} )
        """
        url = f"{cls.BASE_URL}/issue_statuses.json"
        response = requests.get(url, headers=cls._headers())
        response.raise_for_status()
        json_data = response.json()
        statuses = json_data.get("issue_statuses", [])
        logger.debug(f"statuses: {statuses}")
        return statuses

    # --------------------------------------------
    # wiki

    @classmethod
    def create_or_update_wiki(
        cls, project_identifier: str, title: str, content: str, comments: str = ""
    ):
        """
        Wikiページを作成または更新する

        Args:
            project_identifier (str): プロジェクト識別子
            title (str): Wikiページのタイトル
            content (str): ページ内容(Textile or Markdown)
            comments (str): 更新コメント(任意)

        Returns:
            str: 結果メッセージ
        """
        url = f"{cls.BASE_URL}/projects/{project_identifier}/wiki/{title}.json"
        payload = {"wiki_page": {"text": content, "comments": comments}}
        response = requests.put(url, headers=cls._headers(), json=payload)
        logger.info(
            f"Creating or updating wiki page: {title}, project: {project_identifier}"
        )
        response.raise_for_status()
        logger.debug(f"json_data: {response.text}")
        return True

    @classmethod
    def get_wiki(cls, project_identifier: str, title: str):
        """
        Wikiページの内容を取得する

        Args:
            project_identifier (str): プロジェクト識別子
            title (str): ページ名

        Returns:
            dict: ページ内容(text, commentsなど)
        """
        url = f"{cls.BASE_URL}/projects/{project_identifier}/wiki/{title}.json"
        response = requests.get(url, headers=cls._headers())
        response.raise_for_status()
        json_data = response.json()
        logger.debug(f"json_data: {json_data}")
        return json_data.get("wiki_page")

    # --------------------------------------------
    # version file
    @classmethod
    def create_project_file_content(
        cls,
        project_identifier: str,
        file_content: bytes,
        filename: str,
        version_name: str = "ファイルアップロード",
        content_type: str = "application/octet-stream",
    ):
        """
        プロジェクトの「ファイル」タブに file_content を使ってファイルをアップロード

        Args:
            project_identifier (str): プロジェクト識別子
            file_content (bytes): ファイルのバイナリデータ
            filename (str): ファイル名
            version_name (str): バージョン名
            content_type (str): Content-Type(例: application/pdf)

        Returns:
            dict: アップロード結果のJSON
        """
        # 1. アップロードして token を取得
        upload_url = f"{cls.BASE_URL}/uploads.json"
        response = requests.post(
            upload_url,
            headers={**cls._headers(), "Content-Type": "application/octet-stream"},
            data=file_content,
        )
        response.raise_for_status()
        token = response.json()["upload"]["token"]
        logger.info(f"Uploaded {filename}, token: {token}")

        # 最後のファイル登録処理(ファイルタブに表示させる)
        file_post_url = f"{cls.BASE_URL}/projects/{project_identifier}/files.json"
        file_post_payload = {
            "file": {
                "token": token,
                "filename": filename,
                "content_type": content_type,
                "description": "ADK Dockerfile",
                # "version_id": version_id  # 任意
            }
        }
        response = requests.post(
            file_post_url, headers=cls._headers(), json=file_post_payload
        )
        response.raise_for_status()
        return True

    @classmethod
    def create_project_file(
        cls,
        project_identifier: str,
        filepath: str,
        version_name: str = "ファイルアップロード",
        content_type: str = None,
    ):
        """
        ファイルパスからプロジェクトの「ファイル」タブにアップロード

        Args:
            project_identifier (str): プロジェクト識別子
            filepath (str): ファイルパス
            version_name (str): バージョン名(省略可)
            content_type (str): Content-Type(省略時は自動推定)

        Returns:
            dict: アップロード結果のJSON
        """
        filename = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            file_content = f.read()

        # Content-Type 推定(省略時)
        if content_type is None:
            import mimetypes

            content_type = (
                mimetypes.guess_type(filename)[0] or "application/octet-stream"
            )

        return cls.create_project_file_content(
            project_identifier=project_identifier,
            file_content=file_content,
            filename=filename,
            version_name=version_name,
            content_type=content_type,
        )
