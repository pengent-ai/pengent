from typing import Optional
from ....tools.tool_utils import tool
from ...api.project.redmine import ApiRedmine
from ....lib.custom_logger import get_logger

logger = get_logger()


@tool(tags=["redmine", "project_assistant"])
def redmine_get_projects() -> str:
    """
    Redmineのプロジェクト一覧を取得します。

    Returns:
        str: プロジェクトID,プロジェクト識別子とプロジェクト名を含むメッセージ

    """
    try:
        api = ApiRedmine()
        projects = api.get_projects()
        project_list = "\n".join(
            f"{p['id']}:{p['identifier']} {p['name']}" for p in projects
        )
        message = f"プロジェクト一覧:\n{project_list}"
        logger.debug(message)
        return message
    except Exception as e:
        error_message = f"プロジェクトの取得に失敗しました: {str(e)}"
        logger.error(error_message)
        return error_message


@tool(tags=["redmine", "project_assistant"])
def project_create_project(
    name: str,
    identifier: str,
    description: str = "",
    is_public: bool = True,
    parent_id: int = None,
):
    """
    Redmineにプロジェクトを作成します。

    Parameters:
        name (str): プロジェクト名
        identifier (str): プロジェクト識別子
        description (str): プロジェクトの説明(任意)
        is_public (bool): プロジェクトを公開するかどうか(デフォルトはTrue)
        parent_id (int): 親プロジェクトID(Noneの場合はトップレベルとして作成)
    Returns:
        str: 作成されたプロジェクトのIDとURLをメッセージにします
    """
    try:
        api = ApiRedmine()
        project_id = api.create_project(
            name=name,
            identifier=identifier,
            description=description,
            is_public=is_public,
            parent_id=parent_id,
        )
        project_url = f"{ApiRedmine.BASE_URL}/projects/{identifier}"
        message = "プロジェクトが作成されました。\n"
        message += f"ID: {project_id}\nURL: {project_url}"
        logger.debug(message)
        return message
    except Exception as e:
        error_message = f"プロジェクトの作成に失敗しました: {str(e)}"
        logger.error(error_message)
        return error_message


@tool(tags=["redmine", "project_assistant"])
def redmine_create_issues(
    project_identifier: str,
    subject: str,
    description: str,
    assigned_to_id: Optional[int] = None,
    tracker_id: Optional[int] = 1,
    priority_id: Optional[int] = 2,
) -> str:
    """
    Redmineのチケットを作成します。

    Parameters:
        project_identifier (str): プロジェクト識別子
        subject (str): チケットの件名
        description (str): チケットの詳細説明
        assigned_to_id (Optional[int]): 担当者のユーザーID
        tracker_id (Optional[int]): トラッカーID(1: バグ, 2: 機能, 3: サポート)
        priority_id (Optional[int]):優先度(2: 通常, 3: 高, 4: 緊急)
        parent_issue_id (int): 親チケットID(任意)
        due_date (str): 期限日(YYYY-MM-DD)(任意 ISO形式)
        done_ratio (int): 完了率(0-100)(任意)
    Returns:
        str: 作成されたチケットのIDとURLをメッセージにします
    """
    try:
        api = ApiRedmine()
        issue_id = api.create_issue(
            project_identifier=project_identifier,
            subject=subject,
            description=description,
            assigned_to_id=assigned_to_id,
            tracker_id=tracker_id,
            priority_id=priority_id,
        )
        issue_url = f"{ApiRedmine.BASE_URL}/issues/{issue_id}"
        message = f"チケットが作成されました。\nID: {issue_id}\nURL: {issue_url}"
        logger.debug(message)
        return message
    except Exception as e:
        error_message = f"チケットの作成に失敗しました: {str(e)}"
        logger.error(error_message)
        return error_message


@tool(tags=["redmine", "project_assistant"])
def redmine_update_issues(
    issue_id: int,
    subject: str = None,
    description: str = None,
    status_id: int = None,
    assigned_to_id: int = None,
    notes: str = None,
    done_ratio=None,
    due_date=None,
) -> str:
    """
    RedmineのチケットIDに紐づくチケットを更新します。更新したい項目を指定します。

    Parameters:
        issue_id (int): チケットID
        subject (str): 件名(任意)
        description (str): 説明(任意)
        status_id (int): ステータスID
          - 1:起票 2:進行中 3:処理済 4:完了 5:破棄 6:保留
        assigned_to_id (int): 担当者ユーザーID(任意)
        notes (str): コメント(任意)
        done_ratio (int): 完了率(0-100)(任意)
        due_date (str): 期限日(YYYY-MM-DD)(任意 ISO形式)
    Returns:
        str: 更新されたチケットのIDとURLをメッセージにします
    """
    try:
        api = ApiRedmine()
        issue_id = api.update_issue(
            issue_id=issue_id,
            subject=subject,
            description=description,
            assigned_to_id=assigned_to_id,
            status_id=status_id,
            notes=notes,
            done_ratio=done_ratio,
            due_date=due_date,
        )
        issue_url = f"{ApiRedmine.BASE_URL}/issues/{issue_id}"
        message = f"チケットが更新されました。\nID: {issue_id}\nURL: {issue_url}"
        logger.debug(message)
        return message
    except Exception as e:
        error_message = f"チケットの更新に失敗しました: {str(e)}"
        logger.error(error_message)
        return error_message


@tool(tags=["redmine", "project_assistant"])
def redmine_get_issues(
    project_identifier: str,
    status_id: Optional[int] = None,
    assigned_to_id: Optional[int] = None,
) -> str:
    """
    Redmineのプロジェクト識別子に紐づくチケット一覧を取得します。

    Parameters:
        project_identifier (str): プロジェクト識別子
        status_id (Optional[int]): ステータスID
          - 1:起票 2:進行中 3:処理済 4:完了 5:破棄 6:保留
        assigned_to_id (Optional[int]): 担当者ユーザーID(省略可能)
    Returns:
        str: チケットID,件名,ステータスを含むメッセージ
    """
    try:
        api = ApiRedmine()
        issues = api.get_issues(
            project_identifier=project_identifier,
            status_id=status_id,
            assigned_to_id=assigned_to_id,
        )
        issue_list = "\n".join(
            f"{i['id']}: {i['subject']} ({i['status']['name']})" for i in issues
        )
        message = f"チケット一覧:\n{issue_list}"
        logger.debug(message)
        return message
    except Exception as e:
        error_message = f"チケットの取得に失敗しました: {str(e)}"
        logger.error(error_message)
        return error_message


@tool(tags=["redmine", "project_assistant"])
def redmine_show_issue(issue_id: int) -> str:
    """
    RedmineのチケットIDに紐づくチケットの詳細を表示します。

    Parameters:
        issue_id (int): チケットID
    Returns:
        str: チケットの詳細情報を含むメッセージ
    """
    try:
        api = ApiRedmine()
        issue = api.show_issue(issue_id=issue_id)
        message = f"チケット詳細:\nID: {issue['id']}\n"
        message += f"件名: {issue['subject']}\n説明: {issue['description']}\n"
        message += f"ステータス: {issue['status']['name']}"
        logger.debug(message)
        return message
    except Exception as e:
        error_message = f"チケットの取得に失敗しました: {str(e)}"
        logger.error(error_message)
        return error_message


@tool(tags=["redmine"])
def redmine_get_project_members(project_identifier: str) -> str:
    """
    Redmineのプロジェクト識別子に紐づくプロジェクトメンバーを取得します。

    Parameters:
        project_identifier (str): プロジェクト識別子
    Returns:
        str: メンバーID,名前を含むメッセージ
    """
    try:
        api = ApiRedmine()
        members = api.get_project_members(project_identifier=project_identifier)
        member_list = "\n".join(
            f"{m['user']['id']}: {m['user']['name']}" for m in members
        )
        message = f"プロジェクトメンバー一覧:\n{member_list}"
        logger.debug(message)
        return message
    except Exception as e:
        error_message = f"プロジェクトメンバーの取得に失敗しました: {str(e)}"
        logger.error(error_message)
        return error_message
