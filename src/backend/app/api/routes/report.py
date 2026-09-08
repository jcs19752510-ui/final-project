from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status
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


@router.post("/{interview_id}/report", response_model=ReportResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_report(
    interview_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    generator: ReportGenerator = Depends(get_report_generator),
    emotion_analyzer: EmotionAnalyzer = Depends(get_emotion_analyzer),
    prosody_analyzer: ProsodyAnalyzer = Depends(get_prosody_analyzer),
) -> ReportResponse:
    """2026-09-08(u4 TRD §3-1): 무거운 분석(DeepFace/librosa/LLM)을
    백그라운드로 넘기고 즉시 202를 반환 — 운영 환경에서 1분 이상 걸리던
    동기 처리 문제 수정. `should_run`이 True일 때만 백그라운드 작업을
    예약해 중복 실행을 막는다(이미 처리 중이면 현재 상태만 반환)."""
    report, should_run = await report_service.start_report_generation(
        db, interview_id, current_user.id
    )
    if should_run:
        background_tasks.add_task(
            report_service.run_report_generation,
            interview_id,
            generator,
            emotion_analyzer,
            prosody_analyzer,
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
