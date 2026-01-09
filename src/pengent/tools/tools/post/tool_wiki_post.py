from ....tools.tool_utils import tool
from ...api.post.api_wiki_js import ApiWikiJS


@tool(tags=["business_writer"])
def tool_wiki_post(
    title: str,  # 記事のタイトル
    content: str,  # 記事の内容
    path: str,  # 記事のパス(例: "/develop" など 関連性のあるパスを指定)
    description: str,  # 記事の説明
    tags: list[str] = None,  # タグのリスト
    is_draft: bool = False,  # 下書きとして保存するかどうか
):
    """
    WikiJS(内部用Wiki)に記事を投稿する関数

    Args:
        title (str): 記事のタイトル
        content (str): 記事の内容
        path (str): 記事のパス(例:"develop/deploy"など関連性のあるパスを指定)
        description (str): 記事の説明を記載する
        tags (list[str]): タグのリスト (例: ["ビジネス", "文書"])
        is_draft (bool): 下書きとして保存するかどうか(指示がない場合はFalse)

    Returns:
        str: 投稿結果のメッセージ
    """
    try:
        # WikiJSに記事を投稿
        # パスが指定されていない場合は"/public"をデフォルトにする
        path = f"/public/{path}"
        ret = ApiWikiJS.post(
            title=title,
            content=content,
            path=path,
            locale="ja",  # ロケールは日本語に設定
            tags=tags if tags else [],
            description=description,
            editor="markdown",  # エディターの種類を指定
            is_private=is_draft,  # 下書きの場合はプライベートとして扱う
        )
        return f"記事が正常に投稿されました: {ret['page']['path']}"
    except Exception as e:
        return f"記事の投稿中にエラーが発生しました: {str(e)}"


@tool(tags=["business_writer", "search"])
def tool_wiki_search(
    keyword: str,  # 検索キーワード
):
    """
    WikiJS(内部ノウハウ)の記事を検索する関数

    Parameters:
        keyword (str): 検索キーワード

    Returns:
        str: 検索結果のリスト(page_id含む)
    """
    try:
        ret = ApiWikiJS.search(keyword=keyword)
        if not ret:
            return "検索結果はありませんでした。"

        result = "検索結果:\n"
        for item in ret:
            result += f"ID: {item['id']} "
            result += f"パス: {item['path']} タイトル: {item['title']}\n"
            result += f"説明: {item.get('description', 'なし')}\n"
            result += "-" * 20 + "\n"
        return result
    except Exception as e:
        return f"検索中にエラーが発生しました: {str(e)}"


@tool(tags=["business_writer", "search"])
def tool_wiki_show(
    page_id: int,  # ページID
):
    """
    WikiJS(内部ノウハウ)の記事を表示する関数

    Parameters:
        page_id (str): 表示したいページのID

    Returns:
        str: ページの内容
    """
    try:
        ret = ApiWikiJS.show(page_id=page_id)
        return f"ページ内容:\n{ret['content']}"
    except Exception as e:
        return f"ページの取得中にエラーが発生しました: {str(e)}"
