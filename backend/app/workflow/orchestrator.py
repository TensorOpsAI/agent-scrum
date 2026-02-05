"""
Workflow Orchestrator - State machine for story/task transitions with agent handoffs.
"""
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Story, Task, StoryStatus, TaskStatus, AgentType
from app.agents.executor import executor
from app.api.websocket.manager import broadcast_agent_activity


class WorkflowOrchestrator:
    """Orchestrates the workflow by triggering appropriate agents based on state transitions."""

    # Story state machine - maps status to the agent and skill that should handle it
    STORY_HANDLERS: dict[StoryStatus, tuple[AgentType, str] | None] = {
        StoryStatus.BACKLOG: None,  # No automatic action
        StoryStatus.READY_FOR_BREAKDOWN: (AgentType.DEVELOPER, "breakdown_story"),
        StoryStatus.IN_BREAKDOWN: None,  # Developer is working
        StoryStatus.TASKS_IN_REVIEW: (AgentType.TECH_LEAD, "review_tasks"),
        StoryStatus.IN_DEVELOPMENT: None,  # Tasks being worked on
        StoryStatus.IN_QA: None,  # QA testing
        StoryStatus.DONE: None,  # Complete
    }

    # Task state machine - maps status to the agent and skill that should handle it
    TASK_HANDLERS: dict[TaskStatus, tuple[AgentType, str] | None] = {
        TaskStatus.DRAFT: None,  # Waiting for developer
        TaskStatus.PENDING_REVIEW: None,  # Waiting for tech lead (handled at story level)
        TaskStatus.IN_REVIEW: None,  # Tech lead is actively reviewing
        TaskStatus.READY_FOR_DEVELOPMENT: (AgentType.DEVELOPER, "implementation_notes"),
        TaskStatus.IN_PROGRESS: None,  # Developer implementing
        TaskStatus.CODE_REVIEW: (AgentType.CODE_REVIEWER, "review_implementation"),
        TaskStatus.CODE_REVIEW_IN_PROGRESS: None,  # Code reviewer is actively reviewing
        TaskStatus.READY_FOR_QA: (AgentType.QA, "create_test_scenarios"),
        TaskStatus.QA_IN_PROGRESS: (AgentType.QA, "run_tests"),
        TaskStatus.DONE: None,  # Complete
    }

    async def process_story_transition(
        self,
        story: Story,
        old_status: StoryStatus,
        new_status: StoryStatus,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Process a story status transition and trigger appropriate agents."""
        await broadcast_agent_activity(
            "orchestrator",
            "story_transition",
            {
                "story_id": story.id,
                "from": old_status.value,
                "to": new_status.value,
            }
        )

        handler = self.STORY_HANDLERS.get(new_status)
        if not handler:
            return {"triggered": False, "reason": f"No handler for status {new_status}"}

        agent_type, skill = handler

        context = {
            "story_id": story.id,
            "skill": skill,
            "triggered_by": "story_transition",
            "previous_status": old_status.value,
        }

        try:
            result = await executor.execute_agent(
                agent_type=agent_type,
                message=f"Process story #{story.id}: {story.title}",
                context=context,
                db=db,
            )
            return {"triggered": True, "agent": agent_type.value, "result": result}
        except Exception as e:
            return {"triggered": True, "agent": agent_type.value, "error": str(e)}

    async def process_task_transition(
        self,
        task: Task,
        old_status: TaskStatus,
        new_status: TaskStatus,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Process a task status transition and trigger appropriate agents."""
        await broadcast_agent_activity(
            "orchestrator",
            "task_transition",
            {
                "task_id": task.id,
                "from": old_status.value,
                "to": new_status.value,
            }
        )

        handler = self.TASK_HANDLERS.get(new_status)
        if not handler:
            return {"triggered": False, "reason": f"No handler for status {new_status}"}

        agent_type, skill = handler

        context = {
            "task_id": task.id,
            "story_id": task.story_id,
            "skill": skill,
            "triggered_by": "task_transition",
            "previous_status": old_status.value,
        }

        try:
            result = await executor.execute_agent(
                agent_type=agent_type,
                message=f"Process task #{task.id}: {task.title}",
                context=context,
                db=db,
            )
            return {"triggered": True, "agent": agent_type.value, "result": result}
        except Exception as e:
            return {"triggered": True, "agent": agent_type.value, "error": str(e)}

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
        while story.status != StoryStatus.DONE:
            old_status = story.status

            # Trigger story-level handler if available
            result = await self.process_story_transition(
                story, old_status, story.status, db
            )
            results.append({"story_status": story.status.value, **result})

            # Refresh story from DB
            await db.refresh(story)

            # If no handler triggered and not done, process tasks
            if not result.get("triggered") and story.status not in [
                StoryStatus.DONE,
                StoryStatus.IN_BREAKDOWN,
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

        return {"story_id": story_id, "final_status": story.status.value, "steps": results}


# Global orchestrator instance
orchestrator = WorkflowOrchestrator()
