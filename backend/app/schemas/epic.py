from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class EpicCreate(BaseModel):
    title: str
    description: Optional[str] = None
    board_id: int


class EpicUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class EpicResponse(BaseModel):
    id: int
    board_id: int
    title: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    story_count: int = 0

    class Config:
        from_attributes = True
