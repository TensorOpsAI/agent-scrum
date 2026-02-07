from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class StoryBase(BaseModel):
    title: str
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    priority: int = 0


class StoryCreate(StoryBase):
    board_id: int
    epic_id: Optional[int] = None
    prd_content: Optional[str] = None


class StoryUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    priority: Optional[int] = None
    status: Optional[str] = None


class StoryStatusTransition(BaseModel):
    status: str


class StoryResponse(StoryBase):
    id: int
    board_id: int
    epic_id: Optional[int] = None
    status: str
    prd_content: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    task_count: int = 0
    completed_task_count: int = 0

    class Config:
        from_attributes = True


class PRDSubmission(BaseModel):
    content: str
    title: Optional[str] = None
    board_id: int
