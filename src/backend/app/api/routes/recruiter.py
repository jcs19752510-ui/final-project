from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_recruiter
from app.db import get_db
from app.models.user import User
from app.schemas.recruiter import InterviewSummary, StatsResponse
from app.schemas.report import ReportResponse
from app.services import recruiter_service

router = APIRouter(prefix="/api/v1/recruiter", tags=["recruiter"])


@router.get("/interviews", response_model=list[InterviewSummary])
async def list_interviews(
    _recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> list[InterviewSummary]:
    return await recruiter_service.list_interviews(db)


@router.get("/interviews/{interview_id}/report", response_model=ReportResponse)
async def get_report(
    interview_id: UUID,
    _recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    report = await recruiter_service.get_report(db, interview_id)
    return ReportResponse.model_validate(report)


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    _recruiter: User = Depends(require_recruiter),
    db: AsyncSession = Depends(get_db),
) -> StatsResponse:
    return await recruiter_service.get_stats(db)
