"""docs/trd/aimock_u2c_trd.md §3 (2026-09-09 신규, 원안 F-005 착수)."""

import uuid
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.whiteboard import WhiteboardEvaluator
from app.config import settings
from app.core.crypto import encrypt_bytes
from app.core.errors import (
    ForbiddenError,
    NotFoundError,
    PayloadTooLargeError,
    UnsupportedMediaTypeError,
)
from app.models.interview import Interview
from app.models.whiteboard_snapshot import WhiteboardSnapshot

# media_service.py의 F-10 검증 패턴을 그대로 재사용 — 캔버스 PNG 캡처라
# 오디오/영상 프레임보다 훨씬 작을 것으로 예상되어 상한을 더 작게 잡음.
MAX_WHITEBOARD_FILE_BYTES = 10 * 1024 * 1024  # 10MB


def _validate_image(content_type: str | None, size: int) -> None:
    if size > MAX_WHITEBOARD_FILE_BYTES:
        raise PayloadTooLargeError(
            f"이미지가 너무 큽니다({size:,} bytes). "
            f"최대 {MAX_WHITEBOARD_FILE_BYTES:,} bytes({MAX_WHITEBOARD_FILE_BYTES // (1024 * 1024)}MB)까지 허용됩니다."
        )
    if not content_type or not content_type.startswith("image/"):
        raise UnsupportedMediaTypeError(
            f"화이트보드는 이미지 파일만 업로드할 수 있습니다(받은 content-type: {content_type!r})."
        )


def _storage_dir(interview_id: UUID) -> Path:
    d = Path(settings.media_storage_dir) / str(interview_id) / "whiteboard"
    d.mkdir(parents=True, exist_ok=True)
    return d


async def _get_owned_interview(db: AsyncSession, interview_id: UUID, user_id: UUID) -> Interview:
    interview = await db.get(Interview, interview_id)
    if interview is None:
        raise NotFoundError("면접 세션을 찾을 수 없습니다.")
    if interview.candidate_id != user_id:
        raise ForbiddenError("본인 소유의 면접 세션이 아닙니다.")
    return interview


async def submit_whiteboard(
    db: AsyncSession,
    interview_id: UUID,
    user_id: UUID,
    image_bytes: bytes,
    content_type: str | None,
    evaluator: WhiteboardEvaluator,
) -> WhiteboardSnapshot:
    """소유권 확인 → 검증(F-10과 동일 순서 원칙) → 암호화 저장(ADR-004 원칙
    확장, 화이트보드도 지원자가 만든 시각 콘텐츠이므로 동일하게 암호화) →
    Gemini Vision 평가 → 기록."""
    interview = await _get_owned_interview(db, interview_id, user_id)
    _validate_image(content_type, len(image_bytes))

    encrypted = encrypt_bytes(image_bytes)
    filename = f"{uuid.uuid4()}.enc"
    path = _storage_dir(interview_id) / filename
    path.write_bytes(encrypted)

    feedback = await evaluator.evaluate(image_bytes, content_type or "image/png", interview.job_role)

    snapshot = WhiteboardSnapshot(
        interview_id=interview_id,
        image_ref=str(path),
        ai_feedback_text=feedback,
    )
    db.add(snapshot)
    await db.commit()
    await db.refresh(snapshot)
    return snapshot


async def list_whiteboards(db: AsyncSession, interview_id: UUID, user_id: UUID) -> list[WhiteboardSnapshot]:
    await _get_owned_interview(db, interview_id, user_id)
    stmt = (
        select(WhiteboardSnapshot)
        .where(WhiteboardSnapshot.interview_id == interview_id)
        .order_by(WhiteboardSnapshot.created_at)
    )
    return list((await db.scalars(stmt)).all())
