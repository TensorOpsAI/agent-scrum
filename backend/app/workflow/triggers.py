"""
Event-based triggers for workflow state changes.

IMPORTANT: Triggers should ONLY update status. The monitor handles agent dispatching.
This prevents dual-triggering race conditions.
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Story, Task
from app.session import get_current_executor
from app.api.websocket.manager import broadcast_agent_activity
from app.pipeline.templates import get_board, get_template_by_id

logger = logging.getLogger(__name__)


async def on_input_submitted(
    content: str,
    title: str | None,
    board_id: int,
    db: AsyncSession,
) -> dict:
    """Trigger when new input is submitted (PRD, Job Req, Lead List, Incident Report, etc.).

    For internal-source boards (software_dev): dispatches to intake agent to parse input.
    For external-source boards (TA, sales, CISO): creates an Epic from the input.
    """
    logger.info(f"[TRIGGER] on_input_submitted called. Title: {title}, Board: {board_id}, Content length: {len(content)}")

    # Guard: only run if automation is enabled for this board
    board = await get_board(board_id, db)
    if not board or not board.get("agent_automation"):
        logger.info("[TRIGGER] Agent automation disabled, skipping input processing")
        return {"skipped": True, "reason": "Agent automation disabled for this board"}

    await broadcast_agent_activity(
        "trigger",
        "input_submitted",
        {"title": title, "content_length": len(content)}
    )

    # Check if this is an external-source board
    item_source = board.get("item_source", "internal")
    if item_source == "external":
        # For external boards: create an Epic (Position/Account/Threat Category)
        epic_noun = board.get("epic_noun", "Epic")
        epic_title = title or content[:80]
        logger.info(f"[TRIGGER] External board — creating {epic_noun}: {epic_title}")

        from app.db.models import Epic
        epic = Epic(
            board_id=board_id,
            title=epic_title,
            description=content,
        )
        db.add(epic)
        await db.commit()
        await db.refresh(epic)

        logger.info(f"[TRIGGER] Created {epic_noun} #{epic.id}: {epic_title}")
        return {
            "epic_created": True,
            "epic_id": epic.id,
            "epic_title": epic_title,
            "message": f"{epic_noun} created. Use 'Simulate' to generate items.",
        }

    # Internal-source board: dispatch to intake agent
    template_id = board.get("template_id", "software_dev")
    template = get_template_by_id(template_id)
    intake_agent = template.get("intake_agent", "product_owner") if template else "product_owner"

    # Execute the intake agent to parse the input
    context = {
        "skill": "parse_prd",
        "triggered_by": "input_submission",
        "board_id": board_id,
    }

    logger.info(f"[TRIGGER] Calling executor.execute_agent for {intake_agent}...")
    try:
        result = await get_current_executor().execute_agent(
            agent_id=intake_agent,
            message=content,
            context=context,
        )
        logger.info(f"[TRIGGER] executor.execute_agent returned: {result}")
    except Exception as e:
        logger.error(f"[TRIGGER] executor.execute_agent failed: {e}", exc_info=True)
        raise

    return result


# Backward-compatible alias
async def on_prd_submitted(
    prd_content: str,
    title: str | None,
    board_id: int,
    db: AsyncSession,
) -> dict:
    """Backward-compatible alias for on_input_submitted."""
    return await on_input_submitted(
        content=prd_content,
        title=title,
        board_id=board_id,
        db=db,
    )


async def on_story_status_changed(
    story: Story,
    old_status: str,
    new_status: str,
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
            "from": old_status,
            "to": new_status,
        }
    )

    return {"status_changed": True, "new_status": new_status}


async def on_task_status_changed(
    task: Task,
    old_status: str,
    new_status: str,
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
            "from": old_status,
            "to": new_status,
        }
    )

    return {"status_changed": True, "new_status": new_status}


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
        "status": story.status,
        "message": "Workflow will continue on next monitor check"
    }
