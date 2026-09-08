import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, text
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
    # 2026-09-08 추가(리포트 생성 비동기화, aimock_u4_trd.md §3-1): 무거운
    # DeepFace/librosa 분석을 BackgroundTasks로 넘기면서 진행 상태를 추적할
    # 컬럼이 필요해짐. "processing"/"completed"/"failed" 중 하나 — DB
    # CHECK 제약 대신 서비스 계층(`report_service`)에서만 값을 만들어
    # 넣으므로 애플리케이션 레벨로 강제(전역 기술 컨벤션과 동일하게 다른
    # status류 컬럼도 이 프로젝트에서 전부 문자열+애플리케이션 검증 방식).
    status: Mapped[str] = mapped_column(String, nullable=False)
    # 실패 시 사용자에게 보여줄 안전한(내부 스택트레이스 미포함) 메시지.
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # "processing" 상태가 언제 시작됐는지 — 서버 재시작 등으로 백그라운드
    # 작업이 죽어 영원히 "생성 중"에 멈추는 것을 막기 위한 스테일 판정용.
    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # 2026-09-08 버그 수정: server_default="now()"를 문자열로 두면 DDL에서
    # 고정 리터럴로 굳어버림(`app/models/user.py` 주석 참조) — text()로 명시
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
