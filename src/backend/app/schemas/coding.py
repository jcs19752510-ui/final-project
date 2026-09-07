from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class CodeSubmissionRequest(BaseModel):
    language: Literal["python"]
    code: str


class CodeSubmissionResponse(BaseModel):
    submission_id: UUID
    stdout: str
    stderr: str
    exit_code: int | None
    timed_out: bool
