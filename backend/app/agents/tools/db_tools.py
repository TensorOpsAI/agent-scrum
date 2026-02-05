"""
Database Tools - Shared tools for interacting with the database.

These are concrete actions agents can take to read/write data.
"""
import logging
from typing import Optional
from langchain_core.tools import tool
from sqlalchemy import select

from app.db.database import async_session_maker
from app.db.models import Story, Task, Comment, StoryStatus, TaskStatus, AgentType

logger = logging.getLogger(__name__)


# ============================================================================
# Story Tools
# ============================================================================

@tool
async def get_story(story_id: int) -> dict:
    """Fetch a story by ID with its details.

    Args:
        story_id: The ID of the story to fetch

    Returns:
        Dictionary with story details including title, description,
        acceptance_criteria, status, and priority.
    """
    async with async_session_maker() as db:
        result = await db.execute(select(Story).where(Story.id == story_id))
        story = result.scalar_one_or_none()

        if not story:
            return {"error": f"Story {story_id} not found"}

        return {
            "id": story.id,
            "title": story.title,
            "description": story.description,
            "acceptance_criteria": story.acceptance_criteria,
            "status": story.status.value,
            "priority": story.priority,
            "prd_content": story.prd_content,
        }


@tool
async def update_story_status(story_id: int, new_status: str) -> dict:
    """Update a story's status.

    Args:
        story_id: The ID of the story to update
        new_status: The new status (backlog, ready_for_breakdown, in_breakdown,
                   tasks_in_review, in_development, in_qa, done)

    Returns:
        Success/failure message
    """
    async with async_session_maker() as db:
        result = await db.execute(select(Story).where(Story.id == story_id))
        story = result.scalar_one_or_none()

        if not story:
            return {"error": f"Story {story_id} not found"}

        try:
            story.status = StoryStatus(new_status)
            await db.commit()
            await db.refresh(story)

            # Broadcast via WebSocket for real-time updates
            from app.api.websocket.manager import broadcast_story_updated
            await broadcast_story_updated({
                "id": story.id,
                "title": story.title,
                "description": story.description,
                "acceptance_criteria": story.acceptance_criteria,
                "status": story.status.value,
                "priority": story.priority,
            })

            return {"success": True, "message": f"Story {story_id} status updated to {new_status}"}
        except ValueError:
            return {"error": f"Invalid status: {new_status}"}


@tool
async def create_story(
    title: str,
    description: str,
    acceptance_criteria: str,
    priority: int = 1,
    prd_content: str = "",
) -> dict:
    """Create a new user story.

    Args:
        title: The story title (e.g., "As a user, I want...")
        description: Detailed description of the story
        acceptance_criteria: List of acceptance criteria
        priority: Priority level (1=highest, default=1)
        prd_content: Original PRD content if applicable

    Returns:
        The created story details
    """
    logger.info(f"[TOOL:create_story] Called with title: {title[:50]}...")
    try:
        async with async_session_maker() as db:
            story = Story(
                title=title,
                description=description,
                acceptance_criteria=acceptance_criteria,
                priority=priority,
                prd_content=prd_content,
                status=StoryStatus.READY_FOR_BREAKDOWN,
            )
            db.add(story)
            await db.commit()
            await db.refresh(story)
            logger.info(f"[TOOL:create_story] Story created with ID: {story.id}")

            # Broadcast via WebSocket for real-time updates
            from app.api.websocket.manager import broadcast_story_created
            await broadcast_story_created({
                "id": story.id,
                "title": story.title,
                "description": story.description,
                "acceptance_criteria": story.acceptance_criteria,
                "status": story.status.value,
                "priority": story.priority,
            })
            logger.info(f"[TOOL:create_story] WebSocket broadcast sent for story {story.id}")

            return {
                "id": story.id,
                "title": story.title,
                "description": story.description,
                "acceptance_criteria": story.acceptance_criteria,
                "status": story.status.value,
                "priority": story.priority,
            }
    except Exception as e:
        logger.error(f"[TOOL:create_story] Error: {e}", exc_info=True)
        raise


@tool
async def list_stories_by_status(status: str) -> list[dict]:
    """List all stories with a specific status.

    Args:
        status: The status to filter by

    Returns:
        List of stories with that status
    """
    async with async_session_maker() as db:
        try:
            status_enum = StoryStatus(status)
        except ValueError:
            return [{"error": f"Invalid status: {status}"}]

        result = await db.execute(select(Story).where(Story.status == status_enum))
        stories = result.scalars().all()

        return [
            {
                "id": s.id,
                "title": s.title,
                "status": s.status.value,
                "priority": s.priority,
            }
            for s in stories
        ]


# ============================================================================
# Task Tools
# ============================================================================

@tool
async def get_task(task_id: int) -> dict:
    """Fetch a task by ID with its details.

    Args:
        task_id: The ID of the task to fetch

    Returns:
        Dictionary with task details including title, description,
        implementation_notes, test_scenarios, and status.
    """
    async with async_session_maker() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            return {"error": f"Task {task_id} not found"}

        return {
            "id": task.id,
            "story_id": task.story_id,
            "title": task.title,
            "description": task.description,
            "implementation_notes": task.implementation_notes,
            "test_scenarios": task.test_scenarios,
            "status": task.status.value,
            "assigned_agent": task.assigned_agent.value if task.assigned_agent else None,
        }


@tool
async def get_tasks_for_story(story_id: int) -> list[dict]:
    """Get all tasks for a specific story.

    Args:
        story_id: The ID of the story

    Returns:
        List of tasks belonging to the story
    """
    async with async_session_maker() as db:
        result = await db.execute(select(Task).where(Task.story_id == story_id))
        tasks = result.scalars().all()

        return [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "status": t.status.value,
                "implementation_notes": t.implementation_notes,
                "test_scenarios": t.test_scenarios,
            }
            for t in tasks
        ]


@tool
async def create_task(
    story_id: int,
    title: str,
    description: str,
) -> dict:
    """Create a new task for a story.

    Args:
        story_id: The ID of the story this task belongs to
        title: The task title
        description: The task description

    Returns:
        The created task details
    """
    async with async_session_maker() as db:
        task = Task(
            story_id=story_id,
            title=title,
            description=description,
            status=TaskStatus.DRAFT,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        # Broadcast via WebSocket for real-time updates
        from app.api.websocket.manager import broadcast_task_created
        await broadcast_task_created({
            "id": task.id,
            "story_id": task.story_id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
        })

        return {
            "id": task.id,
            "story_id": task.story_id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
        }


@tool
async def update_task_status(task_id: int, new_status: str) -> dict:
    """Update a task's status.

    Args:
        task_id: The ID of the task to update
        new_status: The new status (draft, pending_review, ready_for_development,
                   in_progress, code_review, ready_for_qa, qa_in_progress, done)

    Returns:
        Success/failure message
    """
    async with async_session_maker() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            return {"error": f"Task {task_id} not found"}

        try:
            task.status = TaskStatus(new_status)
            await db.commit()
            await db.refresh(task)

            # Broadcast via WebSocket for real-time updates
            from app.api.websocket.manager import broadcast_task_updated
            await broadcast_task_updated({
                "id": task.id,
                "story_id": task.story_id,
                "title": task.title,
                "description": task.description,
                "status": task.status.value,
                "implementation_notes": task.implementation_notes,
                "test_scenarios": task.test_scenarios,
            })

            return {"success": True, "message": f"Task {task_id} status updated to {new_status}"}
        except ValueError:
            return {"error": f"Invalid status: {new_status}"}


@tool
async def update_task_implementation(task_id: int, implementation_notes: str) -> dict:
    """Update a task's implementation notes.

    Args:
        task_id: The ID of the task to update
        implementation_notes: The implementation notes/code

    Returns:
        Success/failure message
    """
    async with async_session_maker() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            return {"error": f"Task {task_id} not found"}

        task.implementation_notes = implementation_notes
        await db.commit()
        await db.refresh(task)

        # Broadcast via WebSocket for real-time updates
        from app.api.websocket.manager import broadcast_task_updated
        await broadcast_task_updated({
            "id": task.id,
            "story_id": task.story_id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "implementation_notes": task.implementation_notes,
            "test_scenarios": task.test_scenarios,
        })

        return {"success": True, "message": f"Task {task_id} implementation notes updated"}


@tool
async def update_task_test_scenarios(task_id: int, test_scenarios: str) -> dict:
    """Update a task's test scenarios.

    Args:
        task_id: The ID of the task to update
        test_scenarios: The test scenarios

    Returns:
        Success/failure message
    """
    async with async_session_maker() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            return {"error": f"Task {task_id} not found"}

        task.test_scenarios = test_scenarios
        await db.commit()
        await db.refresh(task)

        # Broadcast via WebSocket for real-time updates
        from app.api.websocket.manager import broadcast_task_updated
        await broadcast_task_updated({
            "id": task.id,
            "story_id": task.story_id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "implementation_notes": task.implementation_notes,
            "test_scenarios": task.test_scenarios,
        })

        return {"success": True, "message": f"Task {task_id} test scenarios updated"}


@tool
async def list_tasks_by_status(status: str) -> list[dict]:
    """List all tasks with a specific status.

    Args:
        status: The status to filter by

    Returns:
        List of tasks with that status
    """
    async with async_session_maker() as db:
        try:
            status_enum = TaskStatus(status)
        except ValueError:
            return [{"error": f"Invalid status: {status}"}]

        result = await db.execute(select(Task).where(Task.status == status_enum))
        tasks = result.scalars().all()

        return [
            {
                "id": t.id,
                "story_id": t.story_id,
                "title": t.title,
                "status": t.status.value,
            }
            for t in tasks
        ]


# ============================================================================
# Comment Tools
# ============================================================================

@tool
async def add_comment(
    content: str,
    agent_type: str,
    task_id: Optional[int] = None,
    story_id: Optional[int] = None,
) -> dict:
    """Add a comment to a task or story.

    Args:
        content: The comment content
        agent_type: The type of agent adding the comment
        task_id: Optional task ID (if commenting on a task)
        story_id: Optional story ID (if commenting on a story)

    Returns:
        The created comment details
    """
    async with async_session_maker() as db:
        try:
            agent = AgentType(agent_type)
        except ValueError:
            return {"error": f"Invalid agent type: {agent_type}"}

        comment = Comment(
            content=content,
            agent_type=agent,
            task_id=task_id,
            story_id=story_id,
        )
        db.add(comment)
        await db.commit()
        await db.refresh(comment)

        return {
            "id": comment.id,
            "content": comment.content,
            "agent_type": comment.agent_type.value,
            "task_id": comment.task_id,
            "story_id": comment.story_id,
        }


@tool
async def get_task_comments(task_id: int) -> list[dict]:
    """Get all comments for a task.

    Args:
        task_id: The ID of the task

    Returns:
        List of comments on the task
    """
    async with async_session_maker() as db:
        result = await db.execute(
            select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at)
        )
        comments = result.scalars().all()

        return [
            {
                "id": c.id,
                "content": c.content,
                "agent_type": c.agent_type.value,
                "created_at": c.created_at.isoformat(),
            }
            for c in comments
        ]
