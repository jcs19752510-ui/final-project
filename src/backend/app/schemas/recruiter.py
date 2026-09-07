from uuid import UUID

from pydantic import BaseModel


class InterviewSummary(BaseModel):
    interview_id: UUID
    candidate_email: str
    job_role: str
    status: str
    pass_recommendation: bool | None


class StatsResponse(BaseModel):
    total_interviews: int
    completed_interviews: int
    avg_technical_score: float | None
    avg_communication_score: float | None
    avg_cultural_fit_score: float | None
