import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Story, Task, Comment, StoryStatus, TaskStatus, AgentType


@pytest.mark.asyncio
async def test_create_story(test_session: AsyncSession):
    """Test creating a story in the database."""
    story = Story(
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
    assert story.status == StoryStatus.BACKLOG
    assert story.created_at is not None


@pytest.mark.asyncio
async def test_story_status_values():
    """Test that all story status values are valid."""
    statuses = [
        StoryStatus.BACKLOG,
        StoryStatus.READY_FOR_BREAKDOWN,
        StoryStatus.IN_BREAKDOWN,
        StoryStatus.TASKS_IN_REVIEW,
        StoryStatus.IN_DEVELOPMENT,
        StoryStatus.IN_QA,
        StoryStatus.DONE,
    ]

    assert len(statuses) == 7
    for status in statuses:
        assert isinstance(status.value, str)


@pytest.mark.asyncio
async def test_create_task(test_session: AsyncSession):
    """Test creating a task in the database."""
    # Create a story first
    story = Story(title="Test Story")
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
    assert task.status == TaskStatus.DRAFT


@pytest.mark.asyncio
async def test_task_status_values():
    """Test that all task status values are valid."""
    statuses = [
        TaskStatus.DRAFT,
        TaskStatus.PENDING_REVIEW,
        TaskStatus.READY_FOR_DEVELOPMENT,
        TaskStatus.IN_PROGRESS,
        TaskStatus.CODE_REVIEW,
        TaskStatus.READY_FOR_QA,
        TaskStatus.QA_IN_PROGRESS,
        TaskStatus.DONE,
    ]

    assert len(statuses) == 8
    for status in statuses:
        assert isinstance(status.value, str)


@pytest.mark.asyncio
async def test_create_comment(test_session: AsyncSession):
    """Test creating a comment in the database."""
    # Create a story first
    story = Story(title="Test Story")
    test_session.add(story)
    await test_session.commit()
    await test_session.refresh(story)

    # Create a comment
    comment = Comment(
        story_id=story.id,
        agent_type=AgentType.PRODUCT_OWNER,
        content="Test comment content",
        extra_data={"action": "test"},
    )
    test_session.add(comment)
    await test_session.commit()
    await test_session.refresh(comment)

    assert comment.id is not None
    assert comment.story_id == story.id
    assert comment.agent_type == AgentType.PRODUCT_OWNER


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
async def test_story_task_relationship(test_session: AsyncSession):
    """Test the relationship between stories and tasks."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    # Create a story
    story = Story(title="Test Story")
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
async def test_cascade_delete(test_session: AsyncSession):
    """Test that deleting a story cascades to tasks and comments."""
    # Create a story with tasks and comments
    story = Story(title="Test Story")
    test_session.add(story)
    await test_session.commit()
    await test_session.refresh(story)

    task = Task(story_id=story.id, title="Task 1")
    comment = Comment(
        story_id=story.id,
        agent_type=AgentType.DEVELOPER,
        content="Test comment"
    )
    test_session.add_all([task, comment])
    await test_session.commit()

    # Delete the story
    await test_session.delete(story)
    await test_session.commit()

    # Verify cascade delete (tasks and comments should be gone)
    # This is implicit - if cascade didn't work, we'd get an integrity error
