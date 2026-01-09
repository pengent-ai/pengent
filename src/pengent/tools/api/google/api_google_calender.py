import os
import json

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
from typing import Union, List, Optional
from zoneinfo import ZoneInfo  # Python 3.9+


class ApiGooleCalendar:
    """
    GoogleカレンダーAPIを操作するクラス
    """
    def __init__(self, token_file: str = "token.json"):
        if not os.path.exists(token_file):
            raise FileNotFoundError(f"token file not found: {token_file}")
        with open(token_file, "r") as f:
            creds_data = json.load(f)
        self.creds = Credentials.from_authorized_user_info(creds_data)
        self.service = build("calendar", "v3", credentials=self.creds)

    def get_events(
        self,
        calendar_id: str = "primary",
        from_: Optional[Union[str, datetime]] = None,
        to: Optional[Union[str, datetime]] = None,
        max_results: int = 100,
        timezone_str: str = "Asia/Tokyo",
    ) -> list[dict]:
        """
        カレンダーの予定を取得します

        :param calendar_id: カレンダーID (通常は 'primary')
        :param from_: 開始日時(datetime or str)。省略時は1ヶ月前。
        :param to: 終了日時(datetime or str)。Noneなら制限なし。
        :param max_results: 最大取得件数(Google API上限は2500)
        :param timezone_str: タイムゾーン名(Asia/Tokyo など)
        :return: イベントのリスト(辞書形式)
        """

        def to_iso8601(val: Union[datetime, str], tz_str: str) -> str:
            if isinstance(val, datetime):
                if val.tzinfo is None:
                    val = val.replace(tzinfo=ZoneInfo(tz_str))
                return val.isoformat()
            else:
                dt = datetime.fromisoformat(val)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=ZoneInfo(tz_str))
                return dt.isoformat()

        if from_ is None:
            from_ = datetime.now(timezone.utc) - timedelta(days=30)

        time_min = to_iso8601(from_, timezone_str)
        time_max = to_iso8601(to, timezone_str) if to is not None else None

        list_args = {
            "calendarId": calendar_id,
            "timeMin": time_min,
            "maxResults": max_results,
            "singleEvents": True,
            "orderBy": "startTime",
        }
        if time_max:
            list_args["timeMax"] = time_max

        events_result = self.service.events().list(**list_args).execute()

        events = events_result.get("items", [])
        return [
            {
                "summary": e.get("summary", "(タイトルなし)"),
                "start": e["start"].get("dateTime") or e["start"].get("date"),
                "end": e["end"].get("dateTime") or e["end"].get("date"),
                "id": e.get("id"),
            }
            for e in events
        ]

    def create_event(
        self,
        summary: str,
        start: Union[str, datetime],
        end: Union[str, datetime],
        description: str = "",
        location: str = "",
        attendees: List[str] = None,
        timezone_str: str = "Asia/Tokyo",
    ) -> dict:
        """
        Googleカレンダーに予定を追加します

        :param summary: タイトル(例: "会議")
        :param start: 開始日時(datetime型 or 日時文字列)
        :param end: 終了日時(datetime型 or 日時文字列)
        :param description: 説明(任意)
        :param location: 場所(任意)
        :param attendees: メールアドレスのリスト(任意)
        :param timezone_str: タイムゾーン名(例: "Asia/Tokyo")
        :return: 作成されたイベント情報
        """

        def to_iso8601(
            value: Union[str, datetime], timezone_str: str = "Asia/Tokyo"
        ) -> str:
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    value = value.replace(tzinfo=ZoneInfo(timezone_str))
                return value.isoformat()

            elif isinstance(value, str):
                formats = [
                    "%Y-%m-%d %H:%M",
                    "%Y-%m-%dT%H:%M",
                    "%Y/%m/%d %H:%M",
                    "%Y-%m-%d",  # 終日イベントのための日付だけ
                ]
                for fmt in formats:
                    try:
                        dt = datetime.strptime(value, fmt)
                        dt = dt.replace(tzinfo=ZoneInfo(timezone_str))
                        return dt.isoformat()
                    except ValueError:
                        continue

                raise ValueError(
                    f"Invalid date format: {value}\n"
                    f"許容される形式:\n"
                    f" - '2025-05-17 19:00'\n"
                    f" - '2025/05/17 19:00'\n"
                    f" - '2025-05-17T19:00'\n"
                    f" - '2025-05-17'(終日イベント)"
                )

            else:
                raise TypeError("start/end must be datetime or str")

        start_str = to_iso8601(start, timezone_str)
        end_str = to_iso8601(end, timezone_str)

        event = {
            "summary": summary,
            "location": location,
            "description": description,
            "start": {"dateTime": start_str, "timeZone": timezone_str},
            "end": {"dateTime": end_str, "timeZone": timezone_str},
        }

        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]

        created_event = (
            self.service.events().insert(calendarId="primary", body=event).execute()
        )

        return {
            "status": "success",
            "event_id": created_event.get("id"),
            "html_link": created_event.get("htmlLink"),
            "summary": created_event.get("summary"),
            "start": created_event["start"].get("dateTime"),
            "end": created_event["end"].get("dateTime"),
            "attendees": [a.get("email") for a in created_event.get("attendees", [])],
        }

    def delete_event(self, calendar_id: str, event_id: str) -> dict:
        """
        指定したカレンダー内のイベントを削除します。

        :param calendar_id: カレンダーID(通常は 'primary')
        :param event_id: 削除対象イベントのID
        :return: 結果情報
        """
        self.service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return {"status": "deleted", "calendar_id": calendar_id, "event_id": event_id}

    def create_calendar(self, summary: str, timezone_str: str = "Asia/Tokyo") -> dict:
        """
        新しいカレンダーを作成します。
        :param summary: カレンダー名
        :param timezone_str: タイムゾーン(例: "Asia/Tokyo")
        """
        calendar = {"summary": summary, "timeZone": timezone_str}
        created_calendar = self.service.calendars().insert(body=calendar).execute()
        return {
            "calendar_id": created_calendar["id"],
            "summary": created_calendar["summary"],
        }

    def delete_calendar(self, calendar_id: str) -> dict:
        """
        指定したカレンダーを削除します。
        :param calendar_id: カレンダーID(例: 'xxxxxxxx@group.calendar.google.com')
        """
        self.service.calendars().delete(calendarId=calendar_id).execute()
        return {"status": "deleted", "calendar_id": calendar_id}

    def add_member(self, calendar_id: str, email: str, role: str = "writer") -> dict:
        """
        指定カレンダーにユーザーを共有メンバーとして追加します。
        :param calendar_id: 対象カレンダーID
        :param email: 共有相手のGoogleアカウント(メールアドレス)
        :param role: 'reader', 'writer', 'owner' から選択
        """
        rule = {"scope": {"type": "user", "value": email}, "role": role}
        created_rule = (
            self.service.acl().insert(calendarId=calendar_id, body=rule).execute()
        )
        return {
            "status": "added",
            "email": email,
            "role": role,
            "rule_id": created_rule["id"],
        }

    def remove_member(self, calendar_id: str, email: str) -> dict:
        """
        指定カレンダーから共有メンバーを削除します。
        :param calendar_id: 対象カレンダーID
        :param email: 削除するユーザーのGoogleアカウント
        """
        rule_id = f"user:{email}"
        self.service.acl().delete(calendarId=calendar_id, ruleId=rule_id).execute()
        return {"status": "removed", "email": email}

    def get_calendars(self, max_results: int = 100) -> list[dict]:
        """
        自分がアクセス可能なカレンダーの一覧を取得します。
        :param max_results: 最大取得件数(デフォルト: 100)
        :return: カレンダー情報のリスト(ID、名前など)
        """
        result = self.service.calendarList().list(maxResults=max_results).execute()
        calendars = result.get("items", [])

        return [
            {
                "calendar_id": cal["id"],
                "summary": cal.get("summary"),
                "description": cal.get("description", ""),
                "accessRole": cal.get("accessRole"),
                "primary": cal.get("primary", False),
            }
            for cal in calendars
        ]
