import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class MediaAsset(Base):
    """ADR-003 §ERD (2026-09-07 갱신), ADR-004 원본 미디어 보관 정책."""

    __tablename__ = "media_assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String, nullable=False)  # audio/video_frame
    storage_path: Mapped[str] = mapped_column(String, nullable=False)
    encrypted: Mapped[bool] = mapped_column(Boolean, default=True)
    # 2026-09-08 버그 수정: server_default="now()"를 문자열로 두면 DDL에서
    # 고정 리터럴로 굳어버림(`app/models/user.py` 주석 참조) — text()로 명시
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
