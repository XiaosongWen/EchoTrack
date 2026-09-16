from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserRead(BaseModel):
    id: UUID
    username: str | None = None
    email: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
