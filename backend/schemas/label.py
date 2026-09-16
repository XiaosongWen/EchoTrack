from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LabelBase(BaseModel):
    name: str = Field(..., max_length=50)
    color: str = Field(..., max_length=7)
    description: Optional[str] = Field(None, max_length=255)


class LabelCreate(LabelBase):
    pass


class LabelUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=7)
    description: Optional[str] = Field(None, max_length=255)


class LabelResponse(LabelBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EntityLabelAttach(BaseModel):
    entity_type: str = Field(..., max_length=50)
    entity_id: UUID
