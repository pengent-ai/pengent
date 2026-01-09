from ....tools.tool_utils import tool
from ...api.search.api_brave_search import ApiBraveSearch
from ...api.search.api_read_webpage import ApiHtmlReader
# from pengent.tools.api.search.page.api_webpage import ApiWebPage


@tool(tags=["search"])
def tool_search_web_information(
    query: str,  # 検索キーワード
    limit: int = 5,  # 検索結果の最大件数(デフォルトは5)
):
    """
    ウェブの検索エンジンでWEBページを検索する関数

    Parameters:
        query (str): 検索キーワード
        limit (int): 検索結果の最大件数(デフォルトは5)
    Returns:
        str: 検索した結果を返す(最大5件)
    """
    try:
        api = ApiBraveSearch()
        ret = api.search(limit=limit, query=query)
        tmp = "WEBから検索しました\n\n"
        for item in ret:
            tmp += f"Title: {item['title']}\n"
            tmp += f"URL: {item['url']}\n"
            tmp += f"{item['description']}\n"
            tmp += f"{'-' * 10}\n"
        return tmp
    except Exception as e:
        # エラーが発生した場合の処理
        return f"検索中にエラーが発生しました: {str(e)}"


@tool(tags=["search", "article_writer"])
def tool_search_web_page_information(
    url: str,  # ページのURL
):
    """
    指定したウェブページ(HTML)から情報を取得する関数

    Parameters:
        url (str): ページのURL
    Returns:
        str: ページの情報を返す

    Notes:
        この関数は、指定されたURLのウェブページの情報を取得します。
        TODO: チャンクごとに要約を行う処理を実行する
    """
    api = ApiHtmlReader()
    ret = api.get_page_content(url)
    if len(ret) < 1024 * 1024:  # 1MB以下ならそのまま返す
        return f"取得したページ:{url}\n読み込み結果:\n{ret}"
    else:
        return (
            f"取得したページ:{url}\n読み込み結果は長すぎるため、"
            f"要約を行ってください。\n内容の長さ: {len(ret)}文字"
        )
