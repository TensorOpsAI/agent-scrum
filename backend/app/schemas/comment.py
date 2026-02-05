from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Any

from app.db.models import AgentType


class CommentBase(BaseModel):
    content: str
    agent_type: AgentType
    metadata: Optional[dict[str, Any]] = None


class CommentCreate(CommentBase):
    story_id: Optional[int] = None
    task_id: Optional[int] = None


class CommentResponse(CommentBase):
    id: int
    story_id: Optional[int] = None
    task_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
