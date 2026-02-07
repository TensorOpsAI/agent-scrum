import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Story, Task, Comment, StoryStatus, PipelineConfig


async def _get_default_board_id(client: AsyncClient) -> int:
    """Helper: get the ID of the seeded default board."""
    response = await client.get("/api/boards")
    boards = response.json()
    assert len(boards) > 0, "No boards found - seed may have failed"
    return boards[0]["id"]


@pytest.mark.asyncio
async def test_submit_prd_returns_immediately(client: AsyncClient, sample_prd: str):
    """Test that submitting a PRD returns immediately (async processing)."""
    board_id = await _get_default_board_id(client)
    response = await client.post(
        "/api/prd",
        json={"content": sample_prd, "title": "Auth Feature PRD", "board_id": board_id}
    )
    assert response.status_code == 200

    data = response.json()
    # PRD processing is now async - returns immediately with placeholder
    assert "message" in data
    assert "background" in data["message"].lower()
    assert "stories_created" in data
    assert data["stories_created"] == 0  # Stories created async
    assert "stories" in data
    assert data["stories"] == []  # Empty since async


@pytest.mark.asyncio
async def test_submit_prd_accepts_content(client: AsyncClient):
    """Test that PRD submission accepts content and returns success."""
    board_id = await _get_default_board_id(client)
    prd_content = """
    # Product Requirements

    We need to build a user dashboard with analytics.
    Users should be able to view reports and export data.
    Add notification system for alerts.
    """

    response = await client.post(
        "/api/prd",
        json={"content": prd_content, "board_id": board_id}
    )
    assert response.status_code == 200

    data = response.json()
    # PRD is processed asynchronously
    assert "message" in data
    assert data["stories_created"] == 0  # Async processing


@pytest.mark.asyncio
async def test_get_story_comments(client: AsyncClient, test_session: AsyncSession, test_board: PipelineConfig):
    """Test getting comments for a story."""
    # Create a story
    story = Story(
        board_id=test_board.id,
        title="Test Story",
        description="A test story",
        status=StoryStatus.BACKLOG,
    )
    test_session.add(story)
    await test_session.flush()

    # Create comments (agent_type is now a string)
    comment1 = Comment(
        story_id=story.id,
        agent_type="product_owner",
        content="Created this story from PRD",
        extra_data={"action": "created"},
    )
    comment2 = Comment(
        story_id=story.id,
        agent_type="developer",
        content="Starting to break down this story",
        extra_data={"action": "breakdown_started"},
    )
    test_session.add(comment1)
    test_session.add(comment2)
    await test_session.commit()

    # Get comments
    response = await client.get(f"/api/stories/{story.id}/comments")
    assert response.status_code == 200

    comments = response.json()
    assert len(comments) == 2
    assert comments[0]["content"] == "Created this story from PRD"
    assert comments[0]["agent_type"] == "product_owner"
    assert comments[0]["metadata"] == {"action": "created"}
    assert comments[1]["agent_type"] == "developer"


@pytest.mark.asyncio
async def test_get_task_comments(client: AsyncClient, test_session: AsyncSession, test_board: PipelineConfig):
    """Test getting comments for a task."""
    # Create story and task
    story = Story(
        board_id=test_board.id,
        title="Test Story",
        status=StoryStatus.IN_DEVELOPMENT,
    )
    test_session.add(story)
    await test_session.flush()

    task = Task(
        story_id=story.id,
        title="Test Task",
        status="in_progress",
    )
    test_session.add(task)
    await test_session.flush()

    # Create comment
    comment = Comment(
        task_id=task.id,
        agent_type="code_reviewer",
        content="Code looks good! Approved.",
        extra_data={"approved": True},
    )
    test_session.add(comment)
    await test_session.commit()

    # Get comments
    response = await client.get(f"/api/tasks/{task.id}/comments")
    assert response.status_code == 200

    comments = response.json()
    assert len(comments) == 1
    assert comments[0]["content"] == "Code looks good! Approved."
    assert comments[0]["metadata"]["approved"] is True


@pytest.mark.asyncio
async def test_get_comments_nonexistent_story(client: AsyncClient):
    """Test getting comments for a non-existent story returns 404."""
    response = await client.get("/api/stories/9999/comments")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_comments_nonexistent_task(client: AsyncClient):
    """Test getting comments for a non-existent task returns 404."""
    response = await client.get("/api/tasks/9999/comments")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_comment_with_null_metadata(client: AsyncClient, test_session: AsyncSession, test_board: PipelineConfig):
    """Test that comments with null metadata work correctly."""
    story = Story(
        board_id=test_board.id,
        title="Test Story",
        status=StoryStatus.BACKLOG,
    )
    test_session.add(story)
    await test_session.flush()

    comment = Comment(
        story_id=story.id,
        agent_type="qa",
        content="Running tests...",
        extra_data=None,  # Explicitly null
    )
    test_session.add(comment)
    await test_session.commit()

    response = await client.get(f"/api/stories/{story.id}/comments")
    assert response.status_code == 200

    comments = response.json()
    assert len(comments) == 1
    assert comments[0]["metadata"] is None
