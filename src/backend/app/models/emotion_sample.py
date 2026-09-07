import uuid

from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class EmotionSample(Base):
    """ADR-003 §ERD."""

    __tablename__ = "emotion_samples"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False
    )
    transcript_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transcripts.id"), nullable=True
    )
    ts_offset_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    face_emotion_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    pitch: Mapped[float | None] = mapped_column(Float, nullable=True)
    jitter: Mapped[float | None] = mapped_column(Float, nullable=True)
    speech_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
