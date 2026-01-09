from ....tools.tool_utils import tool
from ...api.news.api_news_data import ApiNewsData


@tool(tags=["search", "chat"])
def tool_search_latest_news(category: str = "technology"):
    """
    最新のニュースを取得する関数

    Parameters:
        category (str): ニュースのカテゴリ(例:"technology","business","sports")
    Returns:
        str: 最新のニュースを返す
    """
    api_news = ApiNewsData()
    try:
        news_items = api_news.get_news(
            category=category,
        )
        if not news_items:
            return "最新のニュースはありませんでした。"

        message = "最新のニュース:\n"
        for item in news_items:
            message += f"*<{item['link']}|{item['title']}>*\n{item['description']}\n"
        return message
    except Exception as e:
        return f"ニュースの取得中にエラーが発生しました: {str(e)}"
