import json
from ....tools.tool_utils import tool
from ...api.post.api_qiita import ApiQiita, ApiQiitaTag


@tool(tags=["article_writer"])
def tool_qiita_post(
    title: str,  # 記事のタイトル
    content: str,  # 記事の内容
    tags: list[str] = None,  # タグのリスト
    private: bool = False,  # 非公開記事として投稿するかどうか
):
    """
    Qiitaに記事を投稿する関数

    Parameters:
        title (str): 記事のタイトル
        content (str): 記事の内容
        tags (list[str]): タグのリスト (例: ["Python", "AI"])
        private (bool): 非公開記事として投稿するかどうか(指示がない場合はFalse)
    """
    try:
        # Qiitaに記事を投稿
        qiita_tags = [ApiQiitaTag(name=tag) for tag in (tags if tags else [])]
        ret = ApiQiita.post(
            title=title,
            content=content,
            tags=qiita_tags,
            private=private,  # 非公開記事として投稿するかどうか
        )
        return f"記事が正常に投稿されました: {ret['url']}"
    except Exception as e:
        return f"記事の投稿中にエラーが発生しました: {str(e)}"


@tool(tags=["article_writer"])
def tool_qiita_search(
    query: str = None,  # タグのリスト
):
    """
    Qiitaの記事を検索する関数

    Parameters:
        query (str): 検索クエリ(例: "Python"や"AI")

    Returns:
        str: 検索結果のリスト
    """
    try:
        # Qiitaの記事を検索
        ret = ApiQiita.get_posts(tag_query=query)
        if not ret:
            return "検索結果はありませんでした。"
        return f"検索結果:\n{json.dumps(ret, ensure_ascii=False, indent=2)}"
    except Exception as e:
        return f"記事の検索中にエラーが発生しました: {str(e)}"


@tool(tags=["article_writer"])
def tool_qiita_get_trend_tags():
    """
    Qiitaのトレンドタグを取得する関数

    Returns:
        str: トレンドタグのリスト
    """
    try:
        # Qiitaのトレンドタグを取得
        trends = ApiQiita.get_trend_tags(stocks_over=100, limit=10)
        if not trends:
            return "トレンドタグはありませんでした。"
        message = "トレンドタグ:\n"
        for tag, count in trends:
            message += f"*{tag}* - {count} count\n"
        return message
    except Exception as e:
        return f"トレンドタグの取得中にエラーが発生しました: {str(e)}"
