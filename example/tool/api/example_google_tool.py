import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
)

from pengent.lib import get_logger

logger = get_logger(level=10)

from dotenv import load_dotenv

load_dotenv()
from pengent.tools.api.google.api_google_calender import ApiGooleCalendar
from pengent.tools.api.google.api_google_mail import ApiGoogleMail
from pengent.tools.api.google.api_google_drive import ApiGoogleDrive
from pengent.tools.api.google.api_google_slides import ApiGoogleSlides


def example_calendar():
    api = ApiGooleCalendar()
    # res = api.get_events()
    # logger.debug(res)
    # res = api.create_event(
    #     summary="飲み会",
    #     start="2025-05-17 19:00",
    #     end="2025-05-18 02:00",
    #     description="地元の飲み会",
    #     location="居酒屋",
    # )
    res = api.get_calendars()
    print(res)


def example_mail():
    api = ApiGoogleMail()
    res = api.send_mail(
        to="info@example.com", subject="テストメール", body="これはテストメールです。"
    )
    print(res)


def example_drive():
    api = ApiGoogleDrive()
    res = api.list_files()
    print(res)


def example_slide():
    api = ApiGoogleSlides()
    # ret = api.create_presentation(
    #     title="自動生成されたプレゼン資料"
    # )
    # print("作成したプレゼンID:", ret)
    presentation_id = "1YfyiGWlkpI1tZPZUfiBSaNe_bcSJRqpFJoMfXzsTM04"
    # ret = api.add_slide(presentation_id,
    #             # layout="BLANK",
    #             title="1ページ目",
    #             body="これは本文です")
    # print("スライドを追加しました",ret)
    # ret = api.get_slides("1YfyiGWlkpI1tZPZUfiBSaNe_bcSJRqpFJoMfXzsTM04")
    # print("スライドID一覧:", ret)

    # slide_object_id = "SLIDES_API144031844_0"
    # ret = api.show_slide(presentation_id, slide_object_id)
    # print("スライドの詳細情報:", ret)

    # スライドの中身をクリアにする
    slide_object_id = "SLIDES_API1912535634_0"
    api.clear_slide(presentation_id, slide_object_id)

    api.add_text_box(
        presentation_id,
        slide_object_id,
        component={
            "text": "自動生成された提案書のタイトル1",
        },
    )

    api.add_text_box(
        presentation_id,
        slide_object_id,
        component={
            "text": "自動生成された提案書のタイトル2",
        },
    )
    # api.add_table(
    #     presentation_id,
    #     slide_object_id,
    #     component={
    #     "data": [
    #         ["氏名", "年齢"],
    #         ["山田太郎", "39"],
    #         ["佐藤花子", "28"]
    #     ],
    #     "position": {"x": 100, "y": 100},
    #     "size": {"width": 400, "height": 200},
    #     "header_background_color": "#dddddd",  # ← style として認識される
    #     "header_bold": True,
    #     "row_height": 20  # 小さめに設定
    # })

    api.add_shape(
        presentation_id,
        slide_object_id,
        component={
            "shape_type": "RIGHT_ARROW",  # ← 日本語でもOK
            "text": "次へ",
            "position": {"x": 300, "y": 200},
            "size": {"width": 120, "height": 60},
            "fill_color": "#ccf0ff",
            "border_color": "#0099cc",
            "border_weight": 2,
        },
    )


example_slide()
