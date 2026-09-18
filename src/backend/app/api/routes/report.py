from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.schemas.report import ReportResponse
from app.services import report_service
from app.tasks import run_report_generation_task

router = APIRouter(prefix="/api/v1/interviews", tags=["report"])


@router.post("/{interview_id}/report", response_model=ReportResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_report(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """2026-09-08(u4 TRD §3-1): 무거운 분석(DeepFace/librosa/LLM)을
    비동기로 넘기고 즉시 202를 반환 — 운영 환경에서 1분 이상 걸리던 동기
    처리 문제 수정. `should_run`이 True일 때만 작업을 예약해 중복 실행을
    막는다(이미 처리 중이면 현재 상태만 반환).

    2026-09-18(ADR-003 갱신): 실행 수단을 FastAPI `BackgroundTasks`에서
    Celery(`run_report_generation_task`)로 교체 — 원본 계획서 아키텍처
    (Celery+Redis)에 정합을 맞추기 위한 재도입. 태스크는 provider 객체
    대신 `interview_id`(문자열)만 받는다 — provider는 직렬화가 안 되는
    라이브 객체라 워커 프로세스 안에서 직접 다시 조회한다(app/tasks.py)."""
    report, should_run = await report_service.start_report_generation(
        db, interview_id, current_user.id
    )
    if should_run:
        run_report_generation_task.delay(str(interview_id))
    return ReportResponse.model_validate(report)


@router.get("/{interview_id}/report", response_model=ReportResponse)
async def get_report(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    report = await report_service.get_report(db, interview_id, current_user.id)
    return ReportResponse.model_validate(report)
