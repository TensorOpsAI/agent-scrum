import pytest
from httpx import AsyncClient


async def _get_default_board_id(client: AsyncClient) -> int:
    """Helper: get the ID of the seeded default board."""
    response = await client.get("/api/boards")
    boards = response.json()
    assert len(boards) > 0, "No boards found - seed may have failed"
    return boards[0]["id"]


async def _list_agents(client: AsyncClient) -> list[dict]:
    response = await client.get("/api/agents")
    assert response.status_code == 200
    agents = response.json()
    assert len(agents) > 0, "No agents found - seed may have failed"
    return agents


@pytest.mark.asyncio
async def test_list_agents(client: AsyncClient):
    """Test listing all registered agents (only active ones)."""
    board_id = await _get_default_board_id(client)
    agents = await _list_agents(client)

    # IDs should be board-scoped: <type>_<board_id>
    for agent in agents:
        assert agent["id"] == f"{agent['type']}_{board_id}"


@pytest.mark.asyncio
async def test_get_agent_info(client: AsyncClient):
    """Test getting an agent's info."""
    agents = await _list_agents(client)
    first = agents[0]

    response = await client.get(f"/api/agents/{first['id']}")
    assert response.status_code == 200

    data = response.json()
    assert data["type"] == first["type"]
    assert "name" in data
    assert "description" in data
    assert "skills" in data
    assert len(data["skills"]) > 0


@pytest.mark.asyncio
async def test_get_agent_card_not_found(client: AsyncClient):
    """Test getting a non-existent agent returns 404."""
    response = await client.get("/api/agents/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_agent_status(client: AsyncClient):
    """Test getting an agent's status."""
    agents = await _list_agents(client)
    first = agents[0]

    response = await client.get(f"/api/agents/{first['id']}/status")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == first["id"]
    assert data["type"] == first["type"]
    assert data["status"] == "idle"
    assert data["current_task"] is None


@pytest.mark.asyncio
async def test_all_agents_have_valid_info(client: AsyncClient):
    """Test that all agents have valid info."""
    agents = await _list_agents(client)

    for agent in agents:
        response = await client.get(f"/api/agents/{agent['id']}")
        assert response.status_code == 200

        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "description" in data
        assert "skills" in data

        # Verify skills have required fields
        for skill in data["skills"]:
            assert "id" in skill
            assert "name" in skill
            assert "description" in skill
