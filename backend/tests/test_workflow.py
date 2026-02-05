import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Story, Task, StoryStatus, TaskStatus, AgentType
from app.workflow.orchestrator import WorkflowOrchestrator


@pytest.fixture
def orchestrator():
    """Create a workflow orchestrator."""
    return WorkflowOrchestrator()


@pytest.mark.asyncio
async def test_story_handler_mapping(orchestrator):
    """Test that story status handlers are properly defined."""
    assert orchestrator.STORY_HANDLERS[StoryStatus.BACKLOG] is None
    assert orchestrator.STORY_HANDLERS[StoryStatus.READY_FOR_BREAKDOWN] == (
        AgentType.DEVELOPER, "breakdown_story"
    )
    assert orchestrator.STORY_HANDLERS[StoryStatus.TASKS_IN_REVIEW] == (
        AgentType.TECH_LEAD, "review_tasks"
    )
    assert orchestrator.STORY_HANDLERS[StoryStatus.DONE] is None


@pytest.mark.asyncio
async def test_task_handler_mapping(orchestrator):
    """Test that task status handlers are properly defined."""
    assert orchestrator.TASK_HANDLERS[TaskStatus.DRAFT] is None
    assert orchestrator.TASK_HANDLERS[TaskStatus.READY_FOR_DEVELOPMENT] == (
        AgentType.DEVELOPER, "implementation_notes"
    )
    assert orchestrator.TASK_HANDLERS[TaskStatus.CODE_REVIEW] == (
        AgentType.CODE_REVIEWER, "review_implementation"
    )
    assert orchestrator.TASK_HANDLERS[TaskStatus.READY_FOR_QA] == (
        AgentType.QA, "create_test_scenarios"
    )
    assert orchestrator.TASK_HANDLERS[TaskStatus.DONE] is None


@pytest.mark.asyncio
async def test_process_story_transition_no_handler(orchestrator, test_session: AsyncSession):
    """Test processing a story transition with no handler."""
    # Create a story
    story = Story(title="Test Story", status=StoryStatus.BACKLOG)
    test_session.add(story)
    await test_session.commit()
    await test_session.refresh(story)

    # Process transition to backlog (no handler)
    with patch('app.api.websocket.manager.broadcast_agent_activity', new_callable=AsyncMock):
        result = await orchestrator.process_story_transition(
            story,
            StoryStatus.BACKLOG,
            StoryStatus.BACKLOG,
            test_session
        )

    assert result["triggered"] is False
    assert "No handler" in result["reason"]


@pytest.mark.asyncio
async def test_process_task_transition_no_handler(orchestrator, test_session: AsyncSession):
    """Test processing a task transition with no handler."""
    # Create a story and task
    story = Story(title="Test Story")
    test_session.add(story)
    await test_session.commit()
    await test_session.refresh(story)

    task = Task(story_id=story.id, title="Test Task", status=TaskStatus.DRAFT)
    test_session.add(task)
    await test_session.commit()
    await test_session.refresh(task)

    # Process transition to draft (no handler)
    with patch('app.api.websocket.manager.broadcast_agent_activity', new_callable=AsyncMock):
        result = await orchestrator.process_task_transition(
            task,
            TaskStatus.DRAFT,
            TaskStatus.DRAFT,
            test_session
        )

    assert result["triggered"] is False
    assert "No handler" in result["reason"]


@pytest.mark.asyncio
async def test_all_story_statuses_covered(orchestrator):
    """Test that all story statuses have a handler defined (even if None)."""
    for status in StoryStatus:
        assert status in orchestrator.STORY_HANDLERS, f"Missing handler for {status}"


@pytest.mark.asyncio
async def test_all_task_statuses_covered(orchestrator):
    """Test that all task statuses have a handler defined (even if None)."""
    for status in TaskStatus:
        assert status in orchestrator.TASK_HANDLERS, f"Missing handler for {status}"
