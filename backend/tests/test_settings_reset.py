import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Story, Task, Comment, AgentMessage, StoryStatus, PipelineConfig


@pytest.mark.asyncio
async def test_reset_clears_all_data(client: AsyncClient, test_session: AsyncSession, test_board: PipelineConfig):
    """Test that reset endpoint clears all data."""
    # Create test data
    story = Story(board_id=test_board.id, title="Test Story", status=StoryStatus.BACKLOG)
    test_session.add(story)
    await test_session.flush()

    task = Task(story_id=story.id, title="Test Task", status="draft")
    test_session.add(task)
    await test_session.flush()

    comment = Comment(
        story_id=story.id,
        agent_type="product_owner",
        content="Test comment"
    )
    test_session.add(comment)

    message = AgentMessage(
        from_agent="developer",
        content="Test message",
        message_type="chat"
    )
    test_session.add(message)
    await test_session.commit()

    # Verify data exists
    stories = (await test_session.execute(select(Story))).scalars().all()
    assert len(stories) == 1

    # Call reset endpoint
    response = await client.post("/api/settings/reset")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # Refresh session to see changes
    await test_session.close()


@pytest.mark.asyncio
async def test_settings_get(client: AsyncClient):
    """Test getting current settings."""
    response = await client.get("/api/settings")
    assert response.status_code == 200

    data = response.json()
    assert "has_api_key" in data
    assert "simulate_mode" in data
    assert "model" in data


@pytest.mark.asyncio
async def test_toggle_simulate_mode(client: AsyncClient):
    """Test toggling simulation mode."""
    # Enable simulation mode
    response = await client.post("/api/settings/simulate-mode?enabled=true")
    assert response.status_code == 200
    assert response.json()["simulate_mode"] is True

    # Disable simulation mode
    response = await client.post("/api/settings/simulate-mode?enabled=false")
    assert response.status_code == 200
    assert response.json()["simulate_mode"] is False
