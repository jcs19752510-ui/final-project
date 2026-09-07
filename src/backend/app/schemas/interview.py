from uuid import UUID

from pydantic import BaseModel


class StartInterviewRequest(BaseModel):
    job_role: str


class StartInterviewResponse(BaseModel):
    interview_id: UUID
    question_text: str


class TurnResponse(BaseModel):
    question_text: str
    ended: bool
