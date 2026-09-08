from uuid import UUID

from pydantic import BaseModel


class ReportResponse(BaseModel):
    interview_id: UUID
    status: str  # "processing" | "completed" | "failed" — aimock_u4_trd.md §3-1
    technical_score: int | None
    communication_score: int | None
    cultural_fit_score: int | None
    summary_text: str | None
    details_json: dict
    error_message: str | None = None

    model_config = {"from_attributes": True}
