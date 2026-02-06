"""Chat API - Messages between users and agents via A2A protocol."""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.db.database import get_db
from app.db.models import AgentMessage
from app.a2a.router import a2a_router, AGENT_NAMES
from app.a2a.registry import registry
from app.agents.langgraph_agents import AGENT_FACTORIES, get_agent

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessageResponse(BaseModel):
    id: int
    from_agent: str
    from_agent_name: str
    to_agent: str | None
    to_agent_name: str | None
    content: str
    story_id: int | None
    task_id: int | None
    message_type: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=list[ChatMessageResponse])
async def get_chat_messages(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    db: AsyncSession = Depends(get_db),
):
    """Get recent chat messages between agents."""
    result = await db.execute(
        select(AgentMessage)
        .order_by(desc(AgentMessage.created_at))
        .limit(limit)
        .offset(offset)
    )
    messages = result.scalars().all()

    # Reverse to get chronological order
    messages = list(reversed(messages))

    return [
        ChatMessageResponse(
            id=msg.id,
            from_agent=msg.from_agent,
            from_agent_name=AGENT_NAMES.get(msg.from_agent, msg.from_agent.replace("_", " ").title()),
            to_agent=msg.to_agent,
            to_agent_name=AGENT_NAMES.get(msg.to_agent, msg.to_agent.replace("_", " ").title()) if msg.to_agent else None,
            content=msg.content,
            story_id=msg.story_id,
            task_id=msg.task_id,
            message_type=msg.message_type,
            created_at=msg.created_at,
        )
        for msg in messages
    ]


class SendMessageRequest(BaseModel):
    content: str
    to_agent: Optional[str] = None
    story_id: Optional[int] = None
    task_id: Optional[int] = None


class SendMessageResponse(BaseModel):
    success: bool
    message: str
    a2a_task_id: Optional[str] = None
    response: Optional[str] = None


@router.post("/send", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a message from a human user to an agent via A2A protocol."""
    # Default to product_owner if no target specified
    to_agent = request.to_agent or "product_owner"

    # Validate agent exists (accept both built-in roles and board-scoped IDs like "recruiter_3")
    agent = get_agent(to_agent)
    if agent is None and to_agent != "client":
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent: {to_agent}. Valid agents: {list(AGENT_FACTORIES.keys())}",
        )

    # Build context
    context = {}
    if request.story_id:
        context["story_id"] = request.story_id
    if request.task_id:
        context["task_id"] = request.task_id

    try:
        # Send via A2A router
        result_task = await a2a_router.send_to_agent(
            from_agent="client",
            to_agent=to_agent,
            message=request.content,
            context=context,
            db=db,
        )

        # Extract response text from task
        response_text = None
        agent_messages = [m for m in result_task.messages if m.role == "agent"]
        if agent_messages:
            from app.schemas.a2a import TextPart
            last_msg = agent_messages[-1]
            response_text = " ".join(
                p.text for p in last_msg.parts if isinstance(p, TextPart)
            )

        return SendMessageResponse(
            success=True,
            message=f"Message sent to {AGENT_NAMES.get(to_agent, to_agent)}",
            a2a_task_id=result_task.id,
            response=response_text,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send message: {str(e)}",
        )


@router.get("/templates")
async def get_chat_templates():
    """Get pre-built chat message templates for common actions."""
    return [
        {
            "id": "parse_prd",
            "label": "Parse PRD",
            "target_agent": "product_owner",
            "template": "Please analyze this PRD and create user stories:\n\n{prd_content}",
        },
        {
            "id": "breakdown_story",
            "label": "Break Down Story",
            "target_agent": "developer",
            "template": "Please break down story #{story_id} into tasks.",
        },
        {
            "id": "review_tasks",
            "label": "Review Tasks",
            "target_agent": "tech_lead",
            "template": "Please review the tasks for story #{story_id}.",
        },
        {
            "id": "check_status",
            "label": "Check Status",
            "target_agent": "scrum_master",
            "template": "What's the current status of story #{story_id}?",
        },
    ]
