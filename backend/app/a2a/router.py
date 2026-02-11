"""
A2A Message Router - Routes messages between agents using A2A protocol.

This router handles agent-to-agent communication, enabling agents to
collaborate via the A2A protocol while maintaining chat visibility.
"""
import uuid
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AgentMessage
from app.schemas.a2a import (
    A2ATask,
    A2ATaskState,
    Message,
    TextPart,
    DataPart,
)
from app.a2a.registry import registry
from app.api.websocket.manager import broadcast_agent_chat


# Agent display names for chat
AGENT_NAMES = {
    "product_owner": "Product Owner",
    "tech_lead": "Tech Lead",
    "developer": "Developer",
    "code_reviewer": "Code Reviewer",
    "qa": "QA",
    "scrum_master": "Scrum Master",
    "client": "Human",
}


class A2ARouter:
    """Routes A2A messages between agents."""

    def __init__(self):
        self._active_tasks: dict[str, A2ATask] = {}
        self._conversations: dict[str, list[str]] = {}

    async def send_to_agent(
        self,
        from_agent: str,
        to_agent: str,
        message: str,
        context: dict[str, Any],
        db: AsyncSession,
        session_id: str | None = None,
        task_id: str | None = None,
    ) -> A2ATask:
        """Send an A2A message from one agent to another."""
        # Generate IDs
        if not task_id:
            task_id = f"a2a-{uuid.uuid4().hex[:12]}"
        if not session_id:
            session_id = f"session-{uuid.uuid4().hex[:8]}"

        # Create user message
        user_message = Message(
            role="user",
            parts=[TextPart(text=message), DataPart(data=context)] if context else [TextPart(text=message)]
        )

        # Record outgoing message in chat
        await self._record_chat_message(
            from_agent=from_agent,
            to_agent=to_agent,
            content=message,
            context=context,
            db=db,
            message_type="a2a_request",
        )

        # Execute the target agent via session-scoped executor
        try:
            from app.session import get_current_executor
            executor = get_current_executor()

            result = await executor.execute_agent(
                agent_id=to_agent,
                message=message,
                context=context,
            )

            response_text = result.get("response", "")

            # Create agent response message
            agent_message = Message(
                role="agent",
                parts=[TextPart(text=response_text)]
            )

            # Create successful task
            task = A2ATask(
                id=task_id,
                session_id=session_id,
                state=A2ATaskState.COMPLETED,
                messages=[user_message, agent_message],
                metadata={
                    "from_agent": from_agent,
                    "to_agent": to_agent,
                    "context": context,
                },
            )

            # Record response in chat
            if response_text:
                await self._record_chat_message(
                    from_agent=to_agent,
                    to_agent=from_agent,
                    content=response_text,
                    context=context,
                    db=db,
                    message_type="a2a_response",
                )

        except Exception as e:
            # Create failed task
            task = A2ATask(
                id=task_id,
                session_id=session_id,
                state=A2ATaskState.FAILED,
                messages=[user_message],
                metadata={
                    "error": str(e),
                    "from_agent": from_agent,
                    "to_agent": to_agent,
                },
            )

        # Store task
        self._active_tasks[task_id] = task

        # Track conversation
        if session_id not in self._conversations:
            self._conversations[session_id] = []
        if task_id not in self._conversations[session_id]:
            self._conversations[session_id].append(task_id)

        return task

    def get_task(self, task_id: str) -> A2ATask | None:
        """Get an A2A task by ID."""
        return self._active_tasks.get(task_id)

    def get_conversation(self, session_id: str) -> list[A2ATask]:
        """Get all tasks in a conversation."""
        task_ids = self._conversations.get(session_id, [])
        return [self._active_tasks[tid] for tid in task_ids if tid in self._active_tasks]

    async def _record_chat_message(
        self,
        from_agent: str,
        to_agent: str,
        content: str,
        context: dict[str, Any],
        db: AsyncSession,
        message_type: str = "a2a",
    ):
        """Record an A2A message in the chat for visibility."""
        message = AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            content=content,
            story_id=context.get("story_id"),
            task_id=context.get("task_id"),
            message_type=message_type,
        )
        db.add(message)
        await db.flush()
        await db.commit()

        # Broadcast via WebSocket with dynamic name lookup
        from_name = await self._get_agent_display_name(from_agent)
        to_name = await self._get_agent_display_name(to_agent) if to_agent else None

        await broadcast_agent_chat({
            "id": message.id,
            "from_agent": from_agent,
            "from_agent_name": from_name,
            "to_agent": to_agent,
            "to_agent_name": to_name,
            "content": content,
            "story_id": context.get("story_id"),
            "task_id": context.get("task_id"),
            "message_type": message_type,
            "created_at": message.created_at.isoformat(),
        })

    async def _get_agent_display_name(self, agent_id: str) -> str:
        """Get display name for an agent, checking static names then DB."""
        # Check static names first
        if agent_id in AGENT_NAMES:
            return AGENT_NAMES[agent_id]
        # Look up from DynamicAgent table
        try:
            from app.session import get_current_session_maker
            from app.db.models import DynamicAgent
            from sqlalchemy import select
            async with get_current_session_maker()() as db:
                result = await db.execute(
                    select(DynamicAgent.name).where(DynamicAgent.id == agent_id)
                )
                name = result.scalar_one_or_none()
                return name or agent_id.replace("_", " ").title()
        except Exception:
            return agent_id.replace("_", " ").title()
