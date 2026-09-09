from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class CodeSubmissionRequest(BaseModel):
    language: Literal["python", "javascript"]
    code: str


class CodeSubmissionResponse(BaseModel):
    submission_id: UUID
    stdout: str
    stderr: str
    exit_code: int | None
    timed_out: bool
