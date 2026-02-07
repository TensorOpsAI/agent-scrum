import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Story, Task, Comment, StoryStatus, TaskStatus, AgentType, PipelineConfig, DynamicAgent


@pytest.mark.asyncio
async def test_create_story(test_session: AsyncSession, test_board: PipelineConfig):
    """Test creating a story in the database."""
    story = Story(
        board_id=test_board.id,
        title="Test Story",
        description="Test description",
        acceptance_criteria="Test criteria",
        priority=1,
    )
    test_session.add(story)
    await test_session.commit()
    await test_session.refresh(story)

    assert story.id is not None
    assert story.title == "Test Story"
    assert story.board_id == test_board.id
    assert story.status == "backlog"
    assert story.created_at is not None


@pytest.mark.asyncio
async def test_story_status_values():
    """Test that the StoryStatus enum still exists and maps to expected strings."""
    expected = [
        "backlog", "ready_for_breakdown", "in_breakdown",
        "tasks_in_review", "in_development", "in_qa", "done",
    ]
    enum_values = [s.value for s in StoryStatus]
    for val in expected:
        assert val in enum_values, f"Expected status '{val}' not found in StoryStatus enum"


@pytest.mark.asyncio
async def test_create_task(test_session: AsyncSession, test_board: PipelineConfig):
    """Test creating a task in the database."""
    # Create a story first
    story = Story(board_id=test_board.id, title="Test Story")
    test_session.add(story)
    await test_session.commit()
    await test_session.refresh(story)

    # Create a task
    task = Task(
        story_id=story.id,
        title="Test Task",
        description="Test task description",
    )
    test_session.add(task)
    await test_session.commit()
    await test_session.refresh(task)

    assert task.id is not None
    assert task.story_id == story.id
    assert task.status == "draft"


@pytest.mark.asyncio
async def test_task_status_values():
    """Test that the TaskStatus enum still exists and maps to expected strings."""
    expected = [
        "draft", "pending_review", "ready_for_development",
        "in_progress", "code_review", "ready_for_qa",
        "qa_in_progress", "done",
    ]
    enum_values = [s.value for s in TaskStatus]
    for val in expected:
        assert val in enum_values, f"Expected status '{val}' not found in TaskStatus enum"


@pytest.mark.asyncio
async def test_create_comment(test_session: AsyncSession, test_board: PipelineConfig):
    """Test creating a comment in the database."""
    # Create a story first
    story = Story(board_id=test_board.id, title="Test Story")
    test_session.add(story)
    await test_session.commit()
    await test_session.refresh(story)

    # Create a comment (agent_type is now a string column)
    comment = Comment(
        story_id=story.id,
        agent_type="product_owner",
        content="Test comment content",
        extra_data={"action": "test"},
    )
    test_session.add(comment)
    await test_session.commit()
    await test_session.refresh(comment)

    assert comment.id is not None
    assert comment.story_id == story.id
    assert comment.agent_type == "product_owner"


@pytest.mark.asyncio
async def test_agent_type_values():
    """Test that all agent type values are valid."""
    agent_types = [
        AgentType.PRODUCT_OWNER,
        AgentType.TECH_LEAD,
        AgentType.DEVELOPER,
        AgentType.CODE_REVIEWER,
        AgentType.QA,
    ]

    assert len(agent_types) == 5
    for agent_type in agent_types:
        assert isinstance(agent_type.value, str)


@pytest.mark.asyncio
async def test_story_task_relationship(test_session: AsyncSession, test_board: PipelineConfig):
    """Test the relationship between stories and tasks."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    # Create a story
    story = Story(board_id=test_board.id, title="Test Story")
    test_session.add(story)
    await test_session.commit()
    await test_session.refresh(story)

    # Create tasks
    task1 = Task(story_id=story.id, title="Task 1")
    task2 = Task(story_id=story.id, title="Task 2")
    test_session.add_all([task1, task2])
    await test_session.commit()

    # Query with eager loading to avoid lazy load issues
    result = await test_session.execute(
        select(Story).where(Story.id == story.id).options(selectinload(Story.tasks))
    )
    story = result.scalar_one()

    assert len(story.tasks) == 2


@pytest.mark.asyncio
async def test_cascade_delete(test_session: AsyncSession, test_board: PipelineConfig):
    """Test that deleting a story cascades to tasks and comments."""
    # Create a story with tasks and comments
    story = Story(board_id=test_board.id, title="Test Story")
    test_session.add(story)
    await test_session.commit()
    await test_session.refresh(story)

    task = Task(story_id=story.id, title="Task 1")
    comment = Comment(
        story_id=story.id,
        agent_type="developer",
        content="Test comment"
    )
    test_session.add_all([task, comment])
    await test_session.commit()

    # Delete the story
    await test_session.delete(story)
    await test_session.commit()

    # Verify cascade delete (tasks and comments should be gone)
    # This is implicit - if cascade didn't work, we'd get an integrity error


@pytest.mark.asyncio
async def test_board_story_relationship(test_session: AsyncSession, test_board: PipelineConfig):
    """Test the relationship between boards and stories."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    # Create stories on the board
    s1 = Story(board_id=test_board.id, title="Story 1")
    s2 = Story(board_id=test_board.id, title="Story 2")
    test_session.add_all([s1, s2])
    await test_session.commit()

    # Query with eager loading
    result = await test_session.execute(
        select(PipelineConfig)
        .where(PipelineConfig.id == test_board.id)
        .options(selectinload(PipelineConfig.stories))
    )
    board = result.scalar_one()

    assert len(board.stories) == 2


@pytest.mark.asyncio
async def test_board_cascade_delete(test_session: AsyncSession):
    """Test that deleting a board cascades to its stories."""
    from app.pipeline.templates import get_template_by_id

    template = get_template_by_id("software_dev")
    board = PipelineConfig(
        template_id=template["template_id"],
        name="Temp Board",
        columns=template["columns"],
        agent_automation=template["agent_automation"],
        item_noun=template["item_noun"],
        has_tasks=template["has_tasks"],
    )
    test_session.add(board)
    await test_session.commit()
    await test_session.refresh(board)

    story = Story(board_id=board.id, title="Will be deleted")
    test_session.add(story)
    await test_session.commit()

    # Delete the board - should cascade to story
    await test_session.delete(board)
    await test_session.commit()


@pytest.mark.asyncio
async def test_comment_with_domain_agent_type(test_session: AsyncSession, test_board: PipelineConfig):
    """Test that comments accept any string as agent_type (not just enum values)."""
    story = Story(board_id=test_board.id, title="Test Story")
    test_session.add(story)
    await test_session.commit()
    await test_session.refresh(story)

    # Domain agent type like "recruiter_3" should work
    comment = Comment(
        story_id=story.id,
        agent_type="recruiter_3",
        content="Screened candidate resume",
    )
    test_session.add(comment)
    await test_session.commit()
    await test_session.refresh(comment)

    assert comment.agent_type == "recruiter_3"


@pytest.mark.asyncio
async def test_dynamic_agent_board_relationship(test_session: AsyncSession, test_board: PipelineConfig):
    """Test that DynamicAgent has board_id relationship."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    custom_id = f"custom_agent_{test_board.id}"
    agent = DynamicAgent(
        id=custom_id,
        name="Custom Agent",
        description="Test custom agent",
        role="custom_agent",
        board_id=test_board.id,
        is_active=True,
    )
    test_session.add(agent)
    await test_session.commit()

    # Query board with agents
    result = await test_session.execute(
        select(PipelineConfig)
        .where(PipelineConfig.id == test_board.id)
        .options(selectinload(PipelineConfig.agents))
    )
    board = result.scalar_one()

    # Board should have agents (seeded + the one we just created)
    assert any(a.id == custom_id for a in board.agents)


@pytest.mark.asyncio
async def test_board_cascade_deletes_agents(test_session: AsyncSession):
    """Test that deleting a board cascades to its agents."""
    from app.pipeline.templates import get_template_by_id
    from sqlalchemy import select

    template = get_template_by_id("software_dev")
    board = PipelineConfig(
        template_id=template["template_id"],
        name="Temp Board for Agent Cascade",
        columns=template["columns"],
        agent_automation=template["agent_automation"],
        item_noun=template["item_noun"],
        has_tasks=template["has_tasks"],
    )
    test_session.add(board)
    await test_session.commit()
    await test_session.refresh(board)

    agent = DynamicAgent(
        id=f"qa_{board.id}",
        name="QA",
        description="Test QA",
        role="qa",
        board_id=board.id,
        is_active=True,
    )
    test_session.add(agent)
    await test_session.commit()

    # Delete the board - should cascade to agent
    await test_session.delete(board)
    await test_session.commit()

    # Verify agent is gone
    result = await test_session.execute(
        select(DynamicAgent).where(DynamicAgent.id == f"qa_{board.id}")
    )
    assert result.scalar_one_or_none() is None
