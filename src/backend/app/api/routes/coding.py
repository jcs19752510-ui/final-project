from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_code_executor, get_current_user
from app.db import get_db
from app.models.user import User
from app.sandbox.executor import CodeExecutor
from app.schemas.coding import CodeSubmissionRequest, CodeSubmissionResponse
from app.services import coding_service

router = APIRouter(prefix="/api/v1/interviews", tags=["coding"])


@router.post(
    "/{interview_id}/coding-submissions",
    response_model=CodeSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_code(
    interview_id: UUID,
    payload: CodeSubmissionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    executor: CodeExecutor = Depends(get_code_executor),
) -> CodeSubmissionResponse:
    submission, result = await coding_service.submit_code(
        db, interview_id, current_user.id, payload.language, payload.code, executor
    )
    return CodeSubmissionResponse(
        submission_id=submission.id,
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
        timed_out=result.timed_out,
    )
