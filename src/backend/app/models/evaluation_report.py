import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class EvaluationReport(Base):
    """ADR-003 §ERD."""

    __tablename__ = "evaluation_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    technical_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    communication_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cultural_fit_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    details_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    # 2026-09-08 버그 수정: server_default="now()"를 문자열로 두면 DDL에서
    # 고정 리터럴로 굳어버림(`app/models/user.py` 주석 참조) — text()로 명시
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
