from datetime import datetime, timezone
from dataclasses import dataclass, field
from ..message_memory import MessageMemoryBase, HistoryMessageMemory

from typing import Dict


@dataclass
class Session:
    """
    リクエストに関するセッションデータクラス

    Notes:
        - session_id: セッションの一意な識別子
        - user_id: ユーザーの一意な識別子
        - stat: セッションの状態を保持する辞書
        - events: メッセージメモリオブジェクト(MessageMemoryBase)
        - created_at: セッション作成日時(UTC)
        - last_updated_time: セッションの最終更新時間(UNIXタイムスタンプ)
    """

    session_id: str
    user_id: str
    state: Dict = field(default_factory=dict)
    events: MessageMemoryBase = field(default_factory=lambda: HistoryMessageMemory())
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated_time: float = 0.0
