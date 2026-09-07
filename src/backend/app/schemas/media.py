from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MediaAssetResponse(BaseModel):
    id: UUID
    kind: str
    turn_index: int
    created_at: datetime

    model_config = {"from_attributes": True}
