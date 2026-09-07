from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.schemas.media import MediaAssetResponse
from app.services import media_service

router = APIRouter(tags=["media"])


@router.get(
    "/api/v1/interviews/{interview_id}/media",
    response_model=list[MediaAssetResponse],
)
async def list_media(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await media_service.list_media(db, interview_id, current_user.id)


@router.post(
    "/api/v1/interviews/{interview_id}/media",
    response_model=MediaAssetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_media(
    interview_id: UUID,
    kind: str = Form(...),
    turn_index: int = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    raw = await file.read()
    return await media_service.upload_media(
        db, interview_id, current_user.id, kind, turn_index, raw
    )


@router.delete("/api/v1/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    media_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await media_service.delete_media(db, media_id, current_user.id)
