import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class WhiteboardSnapshot(Base):
    """ADR-003 §ERD. (Could-have — U2-c에서 실제 사용)"""

    __tablename__ = "whiteboard_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False
    )
    image_ref: Mapped[str] = mapped_column(String, nullable=False)
    ai_feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 2026-09-08 버그 수정: server_default="now()"를 문자열로 두면 DDL에서
    # 고정 리터럴로 굳어버림(`app/models/user.py` 주석 참조) — text()로 명시
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
