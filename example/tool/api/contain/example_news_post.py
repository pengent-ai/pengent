import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src")
    )
)

from pengent.lib import get_logger

logger = get_logger(level=10)

from dotenv import load_dotenv

load_dotenv()

from datetime import datetime, timedelta, timezone

from pengent.tools.api.news.api_news_data import ApiNewsData
from pengent.tools.api.chat.api_slack import ApiSlack
from pengent.tools.api.post.api_qiita import ApiQiita


def example():
    """
    最新のITニュースをスラックに送信する
    """
    # APIのインスタンスを作成
    api_news = ApiNewsData()
    api_slack = ApiSlack()
    api_qiita = ApiQiita()
    channel_id = "C08UU2G7P9R"

    # スラックにメッセージを送信
    message = "<!here>\n"
    # 本日の日付 追加
    # 日本時間 (UTC+9)
    JST = timezone(timedelta(hours=9))
    today_str = datetime.now(JST).strftime("%Y年%m月%d日")

    message += f"本日の日付: {today_str}\n"
    message += "最新のITニュースをお届けします。\n"

    # スラックにメッセージを送信(TOP)
    res = api_slack.send_message(channel_id=channel_id, message=message)
    thread_ts = res["ts"]  # スレッド用の timestamp

    # 最新のITニュースを取得
    news_items = api_news.get_news(
        category="technology",  # カテゴリを指定
    )

    # 各ニュースをスレッドに返信形式で投稿
    for item in news_items:
        api_slack.send_message(
            channel_id=channel_id,
            thread_ts=thread_ts,
            message=f"*<{item['link']}|{item['title']}>*\n{item['description']}",
        )

    message = "最新のQiitaのトレンドタグについてお知らせ\n"
    # スラックにメッセージを送信(TOP)
    res = api_slack.send_message(channel_id=channel_id, message=message)
    thread_ts = res["ts"]  # スレッド用の timestamp

    trends = api_qiita.get_trend_tags(stocks_over=100, limit=10)
    message = ""
    for tag, count in trends:
        message += f"*{tag}* - {count} count\n"

    if not message == "":
        api_slack.send_message(
            channel_id=channel_id, thread_ts=thread_ts, message=message
        )


example()
