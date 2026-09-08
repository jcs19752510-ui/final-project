import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    """ADR-003 §ERD, ADR-006(deleted_at/purge_at)."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)  # candidate/recruiter
    # 2026-09-08 버그 수정: SQLAlchemy에 server_default="now()"를 순수
    # 문자열로 주면 DDL에 함수 호출이 아니라 마이그레이션 적용 시점의
    # 고정 리터럴 타임스탬프로 굳어버리는 문제가 실제 DB에서 발견됨
    # (모든 행의 created_at이 최초 `alembic upgrade head` 실행 시각으로
    # 동일하게 찍힘). `text("now()")`로 SQL 함수 호출임을 명시해야 매
    # INSERT마다 실제 시각으로 계산됨 — `내부테스트결과서/` 참조.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    purge_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
