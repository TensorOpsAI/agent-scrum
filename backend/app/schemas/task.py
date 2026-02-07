from datetime import datetime
from pydantic import BaseModel
from typing import Optional


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
    status: Optional[str] = None
    assigned_agent: Optional[str] = None


class TaskStatusTransition(BaseModel):
    status: str


class TaskResponse(TaskBase):
    id: int
    story_id: int
    status: str
    assigned_agent: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
