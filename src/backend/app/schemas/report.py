from uuid import UUID

from pydantic import BaseModel


class ReportResponse(BaseModel):
    interview_id: UUID
    technical_score: int | None
    communication_score: int | None
    cultural_fit_score: int | None
    summary_text: str | None
    details_json: dict

    model_config = {"from_attributes": True}
