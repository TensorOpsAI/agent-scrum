from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from app.db.models import TaskStatus


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    implementation_notes: Optional[str] = None
    test_scenarios: Optional[str] = None


class TaskCreate(TaskBase):
    story_id: int


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    implementation_notes: Optional[str] = None
    test_scenarios: Optional[str] = None
    status: Optional[TaskStatus] = None
    assigned_agent: Optional[str] = None


class TaskStatusTransition(BaseModel):
    status: TaskStatus


class TaskResponse(TaskBase):
    id: int
    story_id: int
    status: TaskStatus
    assigned_agent: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
