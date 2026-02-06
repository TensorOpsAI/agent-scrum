"""
Workflow Orchestrator - State machine for story/task transitions with agent handoffs.

Template-aware: looks up the board's template_id and uses TEMPLATE_WORKFLOWS
to determine which agent should handle each status transition.
"""
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import Story, Task, SoftwareDevStatus, TaskStatus
from app.agents.executor import executor
from app.api.websocket.manager import broadcast_agent_activity
from app.pipeline.templates import get_board, TEMPLATE_WORKFLOWS


class WorkflowOrchestrator:
    """Orchestrates the workflow by triggering appropriate agents based on state transitions."""

    # Legacy story handler mapping (software_dev only) - kept for test backward compat
    STORY_HANDLERS: dict[str, tuple | None] = {
        SoftwareDevStatus.BACKLOG: None,
        SoftwareDevStatus.READY_FOR_BREAKDOWN: ("developer", "breakdown_story"),
        SoftwareDevStatus.IN_BREAKDOWN: None,
        SoftwareDevStatus.TASKS_IN_REVIEW: ("tech_lead", "review_tasks"),
        SoftwareDevStatus.IN_DEVELOPMENT: None,
        SoftwareDevStatus.IN_QA: None,
        SoftwareDevStatus.DONE: None,
    }

    # Legacy task handler mapping (software_dev only) - kept for test backward compat
    TASK_HANDLERS: dict[TaskStatus, tuple | None] = {
        TaskStatus.DRAFT: None,
        TaskStatus.PENDING_REVIEW: None,
        TaskStatus.IN_REVIEW: None,
        TaskStatus.READY_FOR_DEVELOPMENT: ("developer", "implementation_notes"),
        TaskStatus.IN_PROGRESS: None,
        TaskStatus.CODE_REVIEW: ("code_reviewer", "review_implementation"),
        TaskStatus.CODE_REVIEW_IN_PROGRESS: None,
        TaskStatus.READY_FOR_QA: ("qa", "create_test_scenarios"),
        TaskStatus.QA_IN_PROGRESS: ("qa", "run_tests"),
        TaskStatus.DONE: None,
    }

    async def process_story_transition(
        self,
        story: Story,
        old_status: str,
        new_status: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Process a story status transition and trigger appropriate agents."""
        # Guard: only run automation if the story's board supports it
        board = await get_board(story.board_id, db)
        if not board or not board.get("agent_automation"):
            return {"triggered": False, "reason": "Agent automation disabled for this board"}

        await broadcast_agent_activity(
            "orchestrator",
            "story_transition",
            {
                "story_id": story.id,
                "from": old_status,
                "to": new_status,
            }
        )

        # Look up handler from template workflows
        template_id = board.get("template_id", "software_dev")
        workflow = TEMPLATE_WORKFLOWS.get(template_id, {})
        handler = workflow.get("story_handlers", {}).get(new_status)

        if not handler:
            return {"triggered": False, "reason": f"No handler for status {new_status}"}

        agent_role, skill = handler
        agent_id = f"{agent_role}_{story.board_id}"

        context = {
            "story_id": story.id,
            "skill": skill,
            "triggered_by": "story_transition",
            "previous_status": old_status,
        }

        try:
            result = await executor.execute_agent(
                agent_id=agent_id,
                message=f"Process story #{story.id}: {story.title}",
                context=context,
            )
            return {"triggered": True, "agent": agent_role, "result": result}
        except Exception as e:
            return {"triggered": True, "agent": agent_role, "error": str(e)}

    async def process_task_transition(
        self,
        task: Task,
        old_status: TaskStatus,
        new_status: TaskStatus,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Process a task status transition and trigger appropriate agents."""
        # Guard: only run automation if the task's story's board supports it
        story_result = await db.execute(
            select(Story).where(Story.id == task.story_id)
        )
        story = story_result.scalar_one_or_none()
        if not story:
            return {"triggered": False, "reason": "Story not found"}

        board = await get_board(story.board_id, db)
        if not board or not board.get("agent_automation"):
            return {"triggered": False, "reason": "Agent automation disabled for this board"}

        await broadcast_agent_activity(
            "orchestrator",
            "task_transition",
            {
                "task_id": task.id,
                "from": old_status.value,
                "to": new_status.value,
            }
        )

        # Look up handler from template workflows
        template_id = board.get("template_id", "software_dev")
        workflow = TEMPLATE_WORKFLOWS.get(template_id, {})
        handler = workflow.get("task_handlers", {}).get(new_status.value)

        if not handler:
            return {"triggered": False, "reason": f"No handler for status {new_status}"}

        agent_role, skill = handler
        agent_id = f"{agent_role}_{story.board_id}"

        context = {
            "task_id": task.id,
            "story_id": task.story_id,
            "skill": skill,
            "triggered_by": "task_transition",
            "previous_status": old_status.value,
        }

        try:
            result = await executor.execute_agent(
                agent_id=agent_id,
                message=f"Process task #{task.id}: {task.title}",
                context=context,
            )
            return {"triggered": True, "agent": agent_role, "result": result}
        except Exception as e:
            return {"triggered": True, "agent": agent_role, "error": str(e)}

    async def run_full_workflow(
        self,
        story_id: int,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Run the full workflow for a story from its current state to completion.

        This is useful for demo purposes to show the entire flow.
        """
        results = []

        story_result = await db.execute(select(Story).where(Story.id == story_id))
        story = story_result.scalar_one_or_none()
        if not story:
            return {"error": f"Story #{story_id} not found"}

        # Process based on current story status
        while story.status != SoftwareDevStatus.DONE:
            old_status = story.status

            # Trigger story-level handler if available
            result = await self.process_story_transition(
                story, old_status, story.status, db
            )
            results.append({"story_status": story.status, **result})

            # Refresh story from DB
            await db.refresh(story)

            # If no handler triggered and not done, process tasks
            if not result.get("triggered") and story.status not in [
                SoftwareDevStatus.DONE,
                SoftwareDevStatus.IN_BREAKDOWN,
            ]:
                # Get all tasks for the story
                tasks_result = await db.execute(
                    select(Task).where(Task.story_id == story_id)
                )
                tasks = tasks_result.scalars().all()

                for task in tasks:
                    if task.status == TaskStatus.DONE:
                        continue

                    task_result = await self.process_task_transition(
                        task, task.status, task.status, db
                    )
                    results.append({
                        "task_id": task.id,
                        "task_status": task.status.value,
                        **task_result
                    })

                    await db.refresh(task)

            # Refresh story again after task processing
            await db.refresh(story)

            # Safety break to prevent infinite loops
            if len(results) > 50:
                results.append({"warning": "Max iterations reached"})
                break

        return {"story_id": story_id, "final_status": story.status, "steps": results}


# Global orchestrator instance
orchestrator = WorkflowOrchestrator()
