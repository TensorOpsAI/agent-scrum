import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Story, Task, StoryStatus, PipelineConfig
from app.session import (
    UserSession,
    _current_session,
    set_swarm_active,
    is_swarm_active,
)
from app.workflow.orchestrator import WorkflowOrchestrator


@pytest.fixture
def session_ctx():
    """Bind a minimal UserSession to the contextvar (swarm flags are session-scoped)."""
    from app.agents.executor import AgentExecutor

    session = UserSession(
        id="test-session",
        engine=None,
        session_maker=None,
        executor=AgentExecutor(),
    )
    token = _current_session.set(session)
    yield session
    _current_session.reset(token)

# Mock pipeline that has automation enabled (software dev)
MOCK_AUTOMATION_PIPELINE = {
    "template_id": "software_dev",
    "name": "Software Development",
    "agent_automation": True,
    "columns": [
        {"key": "backlog", "label": "Backlog", "color": "bg-gray-600", "position": 0},
    ],
}


@pytest.fixture
def orchestrator():
    """Create a workflow orchestrator."""
    return WorkflowOrchestrator()


@pytest.mark.asyncio
async def test_story_handler_mapping(orchestrator):
    """Test that story status handlers are properly defined."""
    assert orchestrator.STORY_HANDLERS[StoryStatus.BACKLOG] is None
    assert orchestrator.STORY_HANDLERS[StoryStatus.READY_FOR_BREAKDOWN] == (
        "developer", "breakdown_story"
    )
    assert orchestrator.STORY_HANDLERS[StoryStatus.TASKS_IN_REVIEW] == (
        "tech_lead", "review_tasks"
    )
    assert orchestrator.STORY_HANDLERS[StoryStatus.DONE] is None


@pytest.mark.asyncio
async def test_task_handler_mapping(orchestrator):
    """Test that task status handlers are properly defined."""
    assert orchestrator.TASK_HANDLERS["draft"] is None
    assert orchestrator.TASK_HANDLERS["ready_for_development"] == (
        "developer", "implementation_notes"
    )
    assert orchestrator.TASK_HANDLERS["code_review"] == (
        "code_reviewer", "review_implementation"
    )
    assert orchestrator.TASK_HANDLERS["ready_for_qa"] == (
        "qa", "create_test_scenarios"
    )
    assert orchestrator.TASK_HANDLERS["done"] is None


@pytest.mark.asyncio
async def test_process_story_transition_no_handler(orchestrator, test_session: AsyncSession, test_board: PipelineConfig):
    """Test processing a story transition with no handler."""
    # Create a story
    story = Story(board_id=test_board.id, title="Test Story", status="backlog")
    test_session.add(story)
    await test_session.commit()
    await test_session.refresh(story)

    # Process transition to backlog (no handler) - mock get_board to return automation pipeline
    with patch('app.api.websocket.manager.broadcast_agent_activity', new_callable=AsyncMock), \
         patch('app.workflow.orchestrator.get_board', new_callable=AsyncMock, return_value=MOCK_AUTOMATION_PIPELINE):
        result = await orchestrator.process_story_transition(
            story,
            "backlog",
            "backlog",
            test_session
        )

    assert result["triggered"] is False
    assert "No handler" in result["reason"]


@pytest.mark.asyncio
async def test_process_task_transition_no_handler(orchestrator, test_session: AsyncSession, test_board: PipelineConfig):
    """Test processing a task transition with no handler."""
    # Create a story and task
    story = Story(board_id=test_board.id, title="Test Story")
    test_session.add(story)
    await test_session.commit()
    await test_session.refresh(story)

    task = Task(story_id=story.id, title="Test Task", status="draft")
    test_session.add(task)
    await test_session.commit()
    await test_session.refresh(task)

    # Process transition to draft (no handler) - mock get_board to return automation pipeline
    with patch('app.api.websocket.manager.broadcast_agent_activity', new_callable=AsyncMock), \
         patch('app.workflow.orchestrator.get_board', new_callable=AsyncMock, return_value=MOCK_AUTOMATION_PIPELINE):
        result = await orchestrator.process_task_transition(
            task,
            "draft",
            "draft",
            test_session
        )

    assert result["triggered"] is False
    assert "No handler" in result["reason"]


@pytest.mark.asyncio
async def test_all_story_statuses_covered(orchestrator):
    """Test that all software dev story statuses have a handler defined (even if None)."""
    for status in StoryStatus:
        assert status in orchestrator.STORY_HANDLERS, f"Missing handler for {status}"


@pytest.mark.asyncio
async def test_all_task_statuses_covered(orchestrator):
    """Test that all expected task statuses have a handler defined (even if None)."""
    expected_statuses = [
        "draft", "pending_review", "in_review", "ready_for_development",
        "in_progress", "code_review", "code_review_in_progress",
        "ready_for_qa", "qa_in_progress", "done",
    ]
    for status in expected_statuses:
        assert status in orchestrator.TASK_HANDLERS, f"Missing handler for {status}"


@pytest.mark.asyncio
async def test_swarm_active_flag(session_ctx):
    """Test that set_swarm_active / is_swarm_active work correctly."""
    set_swarm_active(False)
    assert is_swarm_active() is False

    set_swarm_active(True)
    assert is_swarm_active() is True

    # Reset
    set_swarm_active(False)


@pytest.mark.asyncio
async def test_execute_agent_skips_when_swarm_inactive(orchestrator, test_session: AsyncSession, session_ctx):
    """Test that execute_agent returns early when swarm is not active."""
    from app.agents.executor import AgentExecutor

    set_swarm_active(False)

    result = await AgentExecutor().execute_agent(
        agent_id="product_owner",
        message="test message",
        context={},
    )

    assert result["skipped"] is True
    assert "not active" in result["response"]

    # Reset
    set_swarm_active(False)


@pytest.mark.asyncio
async def test_trigger_prd_skips_when_swarm_inactive(test_session: AsyncSession, test_board: PipelineConfig, session_ctx):
    """Test that on_prd_submitted returns early when swarm is not active."""
    from app.workflow.triggers import on_prd_submitted

    set_swarm_active(False)

    with patch('app.api.websocket.manager.broadcast_agent_activity', new_callable=AsyncMock), \
         patch('app.workflow.triggers.get_board', new_callable=AsyncMock, return_value=MOCK_AUTOMATION_PIPELINE):
        result = await on_prd_submitted(
            prd_content="As a user I want login",
            title="Login Feature",
            board_id=test_board.id,
            db=test_session,
        )

    assert result["skipped"] is True
    assert "not active" in result["response"]

    # Reset
    set_swarm_active(False)
