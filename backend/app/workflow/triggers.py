"""
Event-based triggers for workflow state changes.

IMPORTANT: Triggers should ONLY update status. The monitor handles agent dispatching.
This prevents dual-triggering race conditions.
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Story, Task, StoryStatus, TaskStatus
from app.agents.executor import executor
from app.api.websocket.manager import broadcast_agent_activity

logger = logging.getLogger(__name__)


async def on_prd_submitted(
    prd_content: str,
    title: str | None,
    db: AsyncSession,
) -> dict:
    """Trigger when a new PRD is submitted.

    Executes Product Owner synchronously to parse PRD and create stories.
    Stories are created in READY_FOR_BREAKDOWN status - monitor will pick them up.
    """
    logger.info(f"[TRIGGER] on_prd_submitted called. Title: {title}, Content length: {len(prd_content)}")

    await broadcast_agent_activity(
        "trigger",
        "prd_submitted",
        {"title": title, "content_length": len(prd_content)}
    )

    # Execute Product Owner agent to parse the PRD
    # This is the ONLY direct agent execution - because PRD submission is user-initiated
    context = {
        "skill": "parse_prd",
        "triggered_by": "prd_submission",
    }

    logger.info("[TRIGGER] Calling executor.execute_agent for product_owner...")
    try:
        result = await executor.execute_agent(
            agent_id="product_owner",
            message=prd_content,
            context=context,
        )
        logger.info(f"[TRIGGER] executor.execute_agent returned: {result}")
    except Exception as e:
        logger.error(f"[TRIGGER] executor.execute_agent failed: {e}", exc_info=True)
        raise

    # Stories are created with READY_FOR_BREAKDOWN status
    # The monitor will pick them up and trigger developer breakdown
    # We do NOT trigger anything else here to avoid dual-triggering

    return result


async def on_story_status_changed(
    story: Story,
    old_status: StoryStatus,
    new_status: StoryStatus,
    db: AsyncSession,
) -> dict:
    """Called when a story's status changes.

    This is informational only - monitor handles agent dispatching.
    """
    await broadcast_agent_activity(
        "orchestrator",
        "story_transition",
        {
            "story_id": story.id,
            "from": old_status.value,
            "to": new_status.value,
        }
    )

    return {"status_changed": True, "new_status": new_status.value}


async def on_task_status_changed(
    task: Task,
    old_status: TaskStatus,
    new_status: TaskStatus,
    db: AsyncSession,
) -> dict:
    """Called when a task's status changes.

    This is informational only - monitor handles agent dispatching.
    """
    await broadcast_agent_activity(
        "orchestrator",
        "task_transition",
        {
            "task_id": task.id,
            "from": old_status.value,
            "to": new_status.value,
        }
    )

    return {"status_changed": True, "new_status": new_status.value}


async def on_tasks_created(
    story_id: int,
    task_ids: list[int],
    db: AsyncSession,
) -> dict:
    """Called when tasks are created for a story.

    This is informational only - monitor handles agent dispatching.
    """
    await broadcast_agent_activity(
        "trigger",
        "tasks_created",
        {"story_id": story_id, "task_count": len(task_ids)}
    )

    return {"tasks_created": len(task_ids)}


async def on_tasks_approved(
    story_id: int,
    db: AsyncSession,
) -> dict:
    """Called when tasks are approved by tech lead.

    This is informational only - monitor handles agent dispatching.
    """
    await broadcast_agent_activity(
        "trigger",
        "tasks_approved",
        {"story_id": story_id}
    )

    return {"approved": True}


async def trigger_continue_workflow(
    story_id: int,
    db: AsyncSession,
) -> dict:
    """Manually trigger workflow continuation for a story.

    This is informational only - the monitor will pick up stuck items.
    Useful for forcing an immediate check rather than waiting for the monitor.
    """
    await broadcast_agent_activity(
        "trigger",
        "workflow_continue",
        {"story_id": story_id}
    )

    story_result = await db.execute(select(Story).where(Story.id == story_id))
    story = story_result.scalar_one_or_none()

    if not story:
        return {"error": f"Story #{story_id} not found"}

    # Touch the updated_at to reset stuck timer, monitor will pick it up
    from datetime import datetime
    story.updated_at = datetime.utcnow()
    await db.commit()

    return {
        "story_id": story_id,
        "status": story.status.value,
        "message": "Workflow will continue on next monitor check"
    }
