import pytest
from httpx import AsyncClient


async def _get_default_board(client: AsyncClient) -> dict:
    """Helper: get the seeded default board (including its columns)."""
    response = await client.get("/api/boards")
    boards = response.json()
    assert len(boards) > 0, "No boards found - seed may have failed"
    return boards[0]


async def _get_default_board_id(client: AsyncClient) -> int:
    board = await _get_default_board(client)
    return board["id"]


@pytest.mark.asyncio
async def test_list_stories_empty(client: AsyncClient):
    """Test listing stories when database is empty."""
    response = await client.get("/api/stories")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_story(client: AsyncClient, sample_story_data):
    """Test creating a new story."""
    board = await _get_default_board(client)
    story_data = {**sample_story_data, "board_id": board["id"]}

    response = await client.post("/api/stories", json=story_data)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == sample_story_data["title"]
    assert data["description"] == sample_story_data["description"]
    assert data["acceptance_criteria"] == sample_story_data["acceptance_criteria"]
    assert data["priority"] == sample_story_data["priority"]
    assert data["board_id"] == board["id"]
    # Automated boards skip straight to the second column so the swarm picks the item up;
    # non-automated boards land in the first column.
    if board.get("agent_automation") and len(board["columns"]) > 1:
        expected_status = board["columns"][1]["key"]
    else:
        expected_status = board["columns"][0]["key"]
    assert data["status"] == expected_status
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
    board = await _get_default_board(client)
    story_data = {**sample_story_data, "board_id": board["id"]}

    # Create a story first
    create_response = await client.post("/api/stories", json=story_data)
    story_id = create_response.json()["id"]

    # Transition to the board's second column
    second_column = board["columns"][1]["key"]
    response = await client.post(
        f"/api/stories/{story_id}/status",
        json={"status": second_column}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == second_column


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
    board = await _get_default_board(client)
    story_data = {**sample_story_data, "board_id": board["id"]}
    # Automated boards default new stories to the second column (see create_story route).
    if board.get("agent_automation") and len(board["columns"]) > 1:
        default_column = board["columns"][1]["key"]
    else:
        default_column = board["columns"][0]["key"]
    next_column = board["columns"][2]["key"]

    # Create two stories with different statuses
    await client.post("/api/stories", json=story_data)

    story2_data = {**story_data, "title": "Story 2"}
    create_response = await client.post("/api/stories", json=story2_data)
    story2_id = create_response.json()["id"]

    # Transition one to the next column
    await client.post(
        f"/api/stories/{story2_id}/status",
        json={"status": next_column}
    )

    # Filter by default column
    response = await client.get(f"/api/stories?status={default_column}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == default_column

    # Filter by next column
    response = await client.get(f"/api/stories?status={next_column}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == next_column


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
