from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class PipelineColumn(BaseModel):
    key: str
    label: str
    color: str
    position: int


class PipelineTemplateResponse(BaseModel):
    template_id: str
    name: str
    columns: list[PipelineColumn]
    agent_automation: bool
    item_noun: str
    has_tasks: bool


class BoardCreateRequest(BaseModel):
    template_id: str
    name: Optional[str] = None


class BoardResponse(BaseModel):
    id: int
    template_id: str
    name: str
    columns: list[PipelineColumn]
    agent_automation: bool
    item_noun: str
    has_tasks: bool
    story_count: int = 0

    class Config:
        from_attributes = True
