"""docs/trd/aimock_u5_trd.md §3. recruiter는 소유권 검사 없이 전체 열람."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.evaluation_report import EvaluationReport
from app.models.interview import Interview
from app.models.user import User
from app.schemas.recruiter import InterviewSummary, StatsResponse


async def list_interviews(db: AsyncSession) -> list[InterviewSummary]:
    stmt = (
        select(Interview, User.email, EvaluationReport.details_json)
        .join(User, Interview.candidate_id == User.id)
        .outerjoin(EvaluationReport, EvaluationReport.interview_id == Interview.id)
    )
    rows = (await db.execute(stmt)).all()

    summaries: list[InterviewSummary] = []
    for interview, candidate_email, details_json in rows:
        pass_recommendation = None
        if details_json is not None:
            pass_recommendation = details_json.get("pass_recommendation")
        summaries.append(
            InterviewSummary(
                interview_id=interview.id,
                candidate_email=candidate_email,
                job_role=interview.job_role,
                status=interview.status,
                pass_recommendation=pass_recommendation,
            )
        )
    return summaries


async def get_report(db: AsyncSession, interview_id: UUID) -> EvaluationReport:
    report = await db.scalar(
        select(EvaluationReport).where(EvaluationReport.interview_id == interview_id)
    )
    if report is None:
        raise NotFoundError("아직 생성된 리포트가 없습니다.")
    return report


async def get_stats(db: AsyncSession) -> StatsResponse:
    total = await db.scalar(select(func.count()).select_from(Interview))
    completed = await db.scalar(
        select(func.count()).select_from(Interview).where(Interview.status == "completed")
    )
    avg_technical, avg_communication, avg_cultural = (
        await db.execute(
            select(
                func.avg(EvaluationReport.technical_score),
                func.avg(EvaluationReport.communication_score),
                func.avg(EvaluationReport.cultural_fit_score),
            )
        )
    ).one()

    return StatsResponse(
        total_interviews=total or 0,
        completed_interviews=completed or 0,
        avg_technical_score=float(avg_technical) if avg_technical is not None else None,
        avg_communication_score=float(avg_communication) if avg_communication is not None else None,
        avg_cultural_fit_score=float(avg_cultural) if avg_cultural is not None else None,
    )
