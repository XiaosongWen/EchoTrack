from datetime import datetime, date
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from schemas.label import LabelResponse


class CommitmentBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    type: str = Field(..., max_length=50) # habit, goal, task, list
    status: str = Field("active", max_length=50) # active, in_progress, archived, completed, paused
    priority: str = Field("none", max_length=50) # none, low, medium, high
    config: Optional[Dict[str, Any]] = None
    due_date: Optional[date] = None
    sort_order: int = 0


class CommitmentCreate(CommitmentBase):
    parent_id: Optional[UUID] = None
    label_ids: Optional[List[UUID]] = Field(default_factory=list)


class CommitmentUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    type: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=50)
    priority: Optional[str] = Field(None, max_length=50)
    config: Optional[Dict[str, Any]] = None
    due_date: Optional[date] = None
    sort_order: Optional[int] = None
    parent_id: Optional[UUID] = None
    label_ids: Optional[List[UUID]] = None


class ProgressMetrics(BaseModel):
    method: str
    done: float
    total: float
    percent: float
    streak: Optional[int] = None


class CommitmentRead(CommitmentBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    parent_id: Optional[UUID] = None
    labels: List[LabelResponse] = Field(default_factory=list)
    
    progress: Optional[ProgressMetrics] = None

    model_config = ConfigDict(from_attributes=True)
