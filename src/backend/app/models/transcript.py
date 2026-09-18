import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Transcript(Base):
    """ADR-003 §ERD."""

    __tablename__ = "transcripts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    speaker: Mapped[str] = mapped_column(String, nullable=False)  # ai/user
    text: Mapped[str] = mapped_column(Text, nullable=False)
    audio_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    # 원본 ERD(계획서 6.1)에 있던 필드인데 구현 시 누락됐던 것을 2026-09-18
    # 재검토에서 발견해 추가(ADR로 제외 결정된 적 없음). speaker="user" 턴에만
    # LLM 평가 결과(evaluation.sentiment_score)로 채워짐 — ai 발화는 항상
    # null. 범위는 기존 technical_accuracy(1~5)와 동일한 척도로 통일해
    # 리포트 화면 등에서 다른 점수와 나란히 보여도 해석이 헷갈리지 않게 함.
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # 대화 순서 정렬을 위해 클라이언트(Python) 시각을 사용 — 같은 트랜잭션 내
    # 여러 INSERT가 server_default now()를 쓰면 전부 같은 값이 되어 순서가
    # 뒤섞이는 문제(aimock_u2a 구현 중 발견)를 피하기 위함.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
