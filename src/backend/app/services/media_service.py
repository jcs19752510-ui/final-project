import os
import uuid
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.crypto import decrypt_bytes, encrypt_bytes
from app.core.errors import (
    ForbiddenError,
    NotFoundError,
    PayloadTooLargeError,
    UnsupportedMediaTypeError,
)
from app.models.interview import Interview
from app.models.media_asset import MediaAsset

# 2026-09-09(보안 강화, F-10 — 전수검사결과_20260909101218.md): 업로드 검증이
# 전무해 인증된 본인이라도 임의 크기/임의 MIME 파일을 계속 올려 Persistent
# Disk(과금 대상, 용량 유한)를 소진시킬 수 있던 문제. `upload_media()`가
# U1-b/U2-a 양쪽 라우트(media.py 직접 업로드, interview.py 턴 오디오)가
# 공유하는 유일한 저장 경로라 여기 한 곳에만 검증을 넣으면 전부 커버된다.
MAX_UPLOAD_FILE_BYTES = 25 * 1024 * 1024  # 파일 1개당 25MB
ALLOWED_KINDS = {"audio", "video_frame"}
# kind별 허용 content-type 접두어 — 정확히 하나의 MIME으로 고정하지 않고
# 접두어만 검사하는 이유: 브라우저 업로드 폴백(<input type=file accept="audio/*">)
# 이 OS/브라우저에 따라 audio/webm, audio/mpeg, audio/wav, audio/x-m4a 등
# 다양한 실제 오디오 MIME을 보낼 수 있어, 이걸 전부 화이트리스트로 나열하면
# 정상 사용자 업로드를 오탐으로 막을 위험이 더 크다고 판단.
_ALLOWED_CONTENT_TYPE_PREFIX = {"audio": "audio/", "video_frame": "image/"}


def _validate_upload(kind: str, content_type: str | None, size: int) -> None:
    if kind not in ALLOWED_KINDS:
        raise UnsupportedMediaTypeError(
            f"지원하지 않는 미디어 종류입니다: {kind!r}. 허용값: {sorted(ALLOWED_KINDS)}"
        )
    if size > MAX_UPLOAD_FILE_BYTES:
        raise PayloadTooLargeError(
            f"파일이 너무 큽니다({size:,} bytes). "
            f"최대 {MAX_UPLOAD_FILE_BYTES:,} bytes({MAX_UPLOAD_FILE_BYTES // (1024 * 1024)}MB)까지 허용됩니다."
        )
    expected_prefix = _ALLOWED_CONTENT_TYPE_PREFIX[kind]
    if not content_type or not content_type.startswith(expected_prefix):
        raise UnsupportedMediaTypeError(
            f"'{kind}' 종류에는 '{expected_prefix}*' 형식의 파일만 업로드할 수 있습니다 "
            f"(받은 content-type: {content_type!r})."
        )


def _storage_dir(interview_id: UUID) -> Path:
    d = Path(settings.media_storage_dir) / str(interview_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


async def _get_owned_interview(db: AsyncSession, interview_id: UUID, user_id: UUID) -> Interview:
    interview = await db.get(Interview, interview_id)
    if interview is None:
        raise NotFoundError("면접 세션을 찾을 수 없습니다.")
    if interview.candidate_id != user_id:
        raise ForbiddenError("본인 소유의 면접 세션이 아닙니다.")
    return interview


async def upload_media(
    db: AsyncSession,
    interview_id: UUID,
    user_id: UUID,
    kind: str,
    turn_index: int,
    raw_bytes: bytes,
    content_type: str | None = None,
) -> MediaAsset:
    """TRD U1-b AC-1: 암호화 후 저장, 평문 저장 금지.

    2026-09-09(F-10): 저장 전에 종류/크기/content-type을 검증한다 —
    `_get_owned_interview`(소유권 확인)보다 먼저 하지 않는 이유는, 검증
    실패 메시지 자체가 "이 interview가 존재하고 내 것인지" 여부보다
    먼저 노출되면 타인 소유 interview_id로도 검증 로직을 정찰하는 데
    쓰일 수 있어서(권한 확인이 항상 최우선이어야 함)."""
    await _get_owned_interview(db, interview_id, user_id)
    _validate_upload(kind, content_type, len(raw_bytes))

    encrypted = encrypt_bytes(raw_bytes)
    filename = f"{uuid.uuid4()}.enc"
    path = _storage_dir(interview_id) / filename
    path.write_bytes(encrypted)

    asset = MediaAsset(
        interview_id=interview_id,
        turn_index=turn_index,
        kind=kind,
        storage_path=str(path),
        encrypted=True,
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


async def list_media(db: AsyncSession, interview_id: UUID, user_id: UUID) -> list[MediaAsset]:
    """리포트 화면에서 지원자가 자신의 원본 미디어 목록을 보고 삭제를
    요청할 수 있게 하기 위한 조회(마스터 TRD AC-M6, 2026-09-08 추가)."""
    await _get_owned_interview(db, interview_id, user_id)
    stmt = select(MediaAsset).where(MediaAsset.interview_id == interview_id).order_by(
        MediaAsset.turn_index
    )
    return list((await db.scalars(stmt)).all())


def read_media_bytes(asset: MediaAsset) -> bytes:
    """U3-b: 리포트 생성 시 저장된 원본 미디어를 다시 읽어 분석기에
    넣기 위한 헬퍼(docs/trd/aimock_u3b_trd.md §3)."""
    encrypted = Path(asset.storage_path).read_bytes()
    return decrypt_bytes(encrypted)


async def delete_media(db: AsyncSession, media_id: UUID, user_id: UUID) -> None:
    """TRD U1-b AC-2/3/4."""
    asset = await db.get(MediaAsset, media_id)
    if asset is None:
        raise NotFoundError("미디어 자산을 찾을 수 없습니다.")

    await _get_owned_interview(db, asset.interview_id, user_id)

    _remove_file_if_exists(asset.storage_path)
    await db.delete(asset)
    await db.commit()


async def purge_user_media(db: AsyncSession, user_id: UUID) -> None:
    """TRD U1-b AC-5 / ADR-006 연쇄 삭제. 계정 파기 스케줄러에서 users 삭제 전에 호출."""
    stmt = select(MediaAsset).join(Interview).where(Interview.candidate_id == user_id)
    assets = list((await db.scalars(stmt)).all())
    for asset in assets:
        _remove_file_if_exists(asset.storage_path)
        await db.delete(asset)
    await db.flush()


def _remove_file_if_exists(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
