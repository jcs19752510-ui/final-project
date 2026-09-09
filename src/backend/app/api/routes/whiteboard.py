from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers import get_whiteboard_evaluator
from app.ai.whiteboard import WhiteboardEvaluator
from app.api.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.schemas.whiteboard import WhiteboardSnapshotResponse
from app.services import whiteboard_service

router = APIRouter(prefix="/api/v1/interviews", tags=["whiteboard"])


@router.get("/{interview_id}/whiteboard-snapshots", response_model=list[WhiteboardSnapshotResponse])
async def list_whiteboard_snapshots(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await whiteboard_service.list_whiteboards(db, interview_id, current_user.id)


@router.post(
    "/{interview_id}/whiteboard-snapshots",
    response_model=WhiteboardSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_whiteboard_snapshot(
    interview_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    evaluator: WhiteboardEvaluator = Depends(get_whiteboard_evaluator),
):
    raw = await file.read()
    return await whiteboard_service.submit_whiteboard(
        db, interview_id, current_user.id, raw, file.content_type, evaluator
    )
