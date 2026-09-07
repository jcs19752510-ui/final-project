from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.emotion import EmotionAnalyzer
from app.ai.prosody import ProsodyAnalyzer
from app.ai.providers import get_emotion_analyzer, get_prosody_analyzer, get_report_generator
from app.ai.report import ReportGenerator
from app.api.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.schemas.report import ReportResponse
from app.services import report_service

router = APIRouter(prefix="/api/v1/interviews", tags=["report"])


@router.post("/{interview_id}/report", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    generator: ReportGenerator = Depends(get_report_generator),
    emotion_analyzer: EmotionAnalyzer = Depends(get_emotion_analyzer),
    prosody_analyzer: ProsodyAnalyzer = Depends(get_prosody_analyzer),
) -> ReportResponse:
    report = await report_service.generate_report(
        db, interview_id, current_user.id, generator, emotion_analyzer, prosody_analyzer
    )
    return ReportResponse.model_validate(report)


@router.get("/{interview_id}/report", response_model=ReportResponse)
async def get_report(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    report = await report_service.get_report(db, interview_id, current_user.id)
    return ReportResponse.model_validate(report)
