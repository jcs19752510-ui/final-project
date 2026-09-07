import os
import uuid
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.crypto import encrypt_bytes
from app.core.errors import ForbiddenError, NotFoundError
from app.models.interview import Interview
from app.models.media_asset import MediaAsset


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
) -> MediaAsset:
    """TRD U1-b AC-1: 암호화 후 저장, 평문 저장 금지."""
    await _get_owned_interview(db, interview_id, user_id)

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
