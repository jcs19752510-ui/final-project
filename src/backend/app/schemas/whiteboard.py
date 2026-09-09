from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class WhiteboardSnapshotResponse(BaseModel):
    id: UUID
    ai_feedback_text: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
