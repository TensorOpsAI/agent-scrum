import pytest
from httpx import AsyncClient

from app.db.models import StoryStatus


async def _get_default_board_id(client: AsyncClient) -> int:
    """Helper: get the ID of the seeded default board."""
    response = await client.get("/api/boards")
    boards = response.json()
    assert len(boards) > 0, "No boards found - seed may have failed"
    return boards[0]["id"]


@pytest.mark.asyncio
async def test_list_stories_empty(client: AsyncClient):
    """Test listing stories when database is empty."""
    response = await client.get("/api/stories")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_story(client: AsyncClient, sample_story_data):
    """Test creating a new story."""
    board_id = await _get_default_board_id(client)
    story_data = {**sample_story_data, "board_id": board_id}

    response = await client.post("/api/stories", json=story_data)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == sample_story_data["title"]
    assert data["description"] == sample_story_data["description"]
    assert data["acceptance_criteria"] == sample_story_data["acceptance_criteria"]
    assert data["priority"] == sample_story_data["priority"]
    assert data["board_id"] == board_id
    assert data["status"] == "backlog"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_get_story(client: AsyncClient, sample_story_data):
    """Test getting a specific story."""
    board_id = await _get_default_board_id(client)
    story_data = {**sample_story_data, "board_id": board_id}

    # Create a story first
    create_response = await client.post("/api/stories", json=story_data)
    story_id = create_response.json()["id"]

    # Get the story
    response = await client.get(f"/api/stories/{story_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == story_id
    assert data["title"] == sample_story_data["title"]


@pytest.mark.asyncio
async def test_get_story_not_found(client: AsyncClient):
    """Test getting a non-existent story."""
    response = await client.get("/api/stories/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_story(client: AsyncClient, sample_story_data):
    """Test updating a story."""
    board_id = await _get_default_board_id(client)
    story_data = {**sample_story_data, "board_id": board_id}

    # Create a story first
    create_response = await client.post("/api/stories", json=story_data)
    story_id = create_response.json()["id"]

    # Update the story
    update_data = {"title": "Updated Title", "priority": 5}
    response = await client.put(f"/api/stories/{story_id}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["priority"] == 5
    # Other fields should remain unchanged
    assert data["description"] == sample_story_data["description"]


@pytest.mark.asyncio
async def test_transition_story_status(client: AsyncClient, sample_story_data):
    """Test transitioning a story's status."""
    board_id = await _get_default_board_id(client)
    story_data = {**sample_story_data, "board_id": board_id}

    # Create a story first
    create_response = await client.post("/api/stories", json=story_data)
    story_id = create_response.json()["id"]

    # Transition status
    response = await client.post(
        f"/api/stories/{story_id}/status",
        json={"status": "ready_for_breakdown"}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ready_for_breakdown"


@pytest.mark.asyncio
async def test_delete_story(client: AsyncClient, sample_story_data):
    """Test deleting a story."""
    board_id = await _get_default_board_id(client)
    story_data = {**sample_story_data, "board_id": board_id}

    # Create a story first
    create_response = await client.post("/api/stories", json=story_data)
    story_id = create_response.json()["id"]

    # Delete the story
    response = await client.delete(f"/api/stories/{story_id}")
    assert response.status_code == 200

    # Verify it's deleted
    get_response = await client.get(f"/api/stories/{story_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_list_stories_by_status(client: AsyncClient, sample_story_data):
    """Test listing stories filtered by status."""
    board_id = await _get_default_board_id(client)
    story_data = {**sample_story_data, "board_id": board_id}

    # Create two stories with different statuses
    await client.post("/api/stories", json=story_data)

    story2_data = {**story_data, "title": "Story 2"}
    create_response = await client.post("/api/stories", json=story2_data)
    story2_id = create_response.json()["id"]

    # Transition one to ready_for_breakdown
    await client.post(
        f"/api/stories/{story2_id}/status",
        json={"status": "ready_for_breakdown"}
    )

    # Filter by backlog
    response = await client.get("/api/stories?status=backlog")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "backlog"

    # Filter by ready_for_breakdown
    response = await client.get("/api/stories?status=ready_for_breakdown")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "ready_for_breakdown"


@pytest.mark.asyncio
async def test_get_story_comments_empty(client: AsyncClient, sample_story_data):
    """Test getting comments for a story with no comments."""
    board_id = await _get_default_board_id(client)
    story_data = {**sample_story_data, "board_id": board_id}

    # Create a story first
    create_response = await client.post("/api/stories", json=story_data)
    story_id = create_response.json()["id"]

    # Get comments
    response = await client.get(f"/api/stories/{story_id}/comments")
    assert response.status_code == 200
    assert response.json() == []
