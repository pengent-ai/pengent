from ..base import Base
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON
from sqlalchemy.sql import func


class SessionORM(Base):
    """セッション情報を格納するORMモデル"""

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String, index=True, nullable=False)
    state = Column(JSON, nullable=True)
    events_max_messages = Column(Integer, nullable=True)
    messages_type = Column(String(20), nullable=True)
    last_updated_time = Column(Float, nullable=False)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
