import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_tasks_empty(client: AsyncClient):
    """Test listing tasks when database is empty."""
    response = await client.get("/api/tasks")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, sample_story_data, sample_task_data):
    """Test creating a new task."""
    # Create a story first
    story_response = await client.post("/api/stories", json=sample_story_data)
    story_id = story_response.json()["id"]

    # Create task
    task_data = {**sample_task_data, "story_id": story_id}
    response = await client.post("/api/tasks", json=task_data)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == sample_task_data["title"]
    assert data["description"] == sample_task_data["description"]
    assert data["story_id"] == story_id
    assert data["status"] == "draft"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_create_task_story_not_found(client: AsyncClient, sample_task_data):
    """Test creating a task for non-existent story."""
    task_data = {**sample_task_data, "story_id": 999}
    response = await client.post("/api/tasks", json=task_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_task(client: AsyncClient, sample_story_data, sample_task_data):
    """Test getting a specific task."""
    # Create a story and task
    story_response = await client.post("/api/stories", json=sample_story_data)
    story_id = story_response.json()["id"]

    task_data = {**sample_task_data, "story_id": story_id}
    task_response = await client.post("/api/tasks", json=task_data)
    task_id = task_response.json()["id"]

    # Get the task
    response = await client.get(f"/api/tasks/{task_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == sample_task_data["title"]


@pytest.mark.asyncio
async def test_get_task_not_found(client: AsyncClient):
    """Test getting a non-existent task."""
    response = await client.get("/api/tasks/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient, sample_story_data, sample_task_data):
    """Test updating a task."""
    # Create a story and task
    story_response = await client.post("/api/stories", json=sample_story_data)
    story_id = story_response.json()["id"]

    task_data = {**sample_task_data, "story_id": story_id}
    task_response = await client.post("/api/tasks", json=task_data)
    task_id = task_response.json()["id"]

    # Update the task
    update_data = {
        "title": "Updated Task Title",
        "implementation_notes": "Some implementation notes"
    }
    response = await client.put(f"/api/tasks/{task_id}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == "Updated Task Title"
    assert data["implementation_notes"] == "Some implementation notes"


@pytest.mark.asyncio
async def test_transition_task_status(client: AsyncClient, sample_story_data, sample_task_data):
    """Test transitioning a task's status."""
    # Create a story and task
    story_response = await client.post("/api/stories", json=sample_story_data)
    story_id = story_response.json()["id"]

    task_data = {**sample_task_data, "story_id": story_id}
    task_response = await client.post("/api/tasks", json=task_data)
    task_id = task_response.json()["id"]

    # Transition status
    response = await client.post(
        f"/api/tasks/{task_id}/status",
        json={"status": "in_progress"}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "in_progress"


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, sample_story_data, sample_task_data):
    """Test deleting a task."""
    # Create a story and task
    story_response = await client.post("/api/stories", json=sample_story_data)
    story_id = story_response.json()["id"]

    task_data = {**sample_task_data, "story_id": story_id}
    task_response = await client.post("/api/tasks", json=task_data)
    task_id = task_response.json()["id"]

    # Delete the task
    response = await client.delete(f"/api/tasks/{task_id}")
    assert response.status_code == 200

    # Verify it's deleted
    get_response = await client.get(f"/api/tasks/{task_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_list_tasks_by_story(client: AsyncClient, sample_story_data, sample_task_data):
    """Test listing tasks filtered by story_id."""
    # Create two stories
    story1_response = await client.post("/api/stories", json=sample_story_data)
    story1_id = story1_response.json()["id"]

    story2_data = {**sample_story_data, "title": "Story 2"}
    story2_response = await client.post("/api/stories", json=story2_data)
    story2_id = story2_response.json()["id"]

    # Create tasks for each story
    task1_data = {**sample_task_data, "story_id": story1_id, "title": "Task 1"}
    await client.post("/api/tasks", json=task1_data)

    task2_data = {**sample_task_data, "story_id": story2_id, "title": "Task 2"}
    await client.post("/api/tasks", json=task2_data)

    # Filter by story1
    response = await client.get(f"/api/tasks?story_id={story1_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Task 1"


@pytest.mark.asyncio
async def test_list_tasks_by_status(client: AsyncClient, sample_story_data, sample_task_data):
    """Test listing tasks filtered by status."""
    # Create a story
    story_response = await client.post("/api/stories", json=sample_story_data)
    story_id = story_response.json()["id"]

    # Create two tasks
    task1_data = {**sample_task_data, "story_id": story_id, "title": "Task 1"}
    task1_response = await client.post("/api/tasks", json=task1_data)
    task1_id = task1_response.json()["id"]

    task2_data = {**sample_task_data, "story_id": story_id, "title": "Task 2"}
    await client.post("/api/tasks", json=task2_data)

    # Transition one to in_progress
    await client.post(f"/api/tasks/{task1_id}/status", json={"status": "in_progress"})

    # Filter by draft
    response = await client.get("/api/tasks?status=draft")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "draft"
