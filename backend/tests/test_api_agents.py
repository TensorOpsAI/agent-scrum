import pytest
from httpx import AsyncClient


async def _get_default_board_id(client: AsyncClient) -> int:
    """Helper: get the ID of the seeded default board."""
    response = await client.get("/api/boards")
    boards = response.json()
    assert len(boards) > 0, "No boards found - seed may have failed"
    return boards[0]["id"]


@pytest.mark.asyncio
async def test_list_agents(client: AsyncClient):
    """Test listing all registered agents (only active ones)."""
    board_id = await _get_default_board_id(client)
    response = await client.get("/api/agents")
    assert response.status_code == 200

    data = response.json()
    # Only 5 active agents by default (scrum_master is inactive)
    assert len(data) == 5

    agent_roles = [agent["type"] for agent in data]
    assert "product_owner" in agent_roles
    assert "tech_lead" in agent_roles
    assert "developer" in agent_roles
    assert "code_reviewer" in agent_roles
    assert "qa" in agent_roles
    # scrum_master is inactive by default
    assert "scrum_master" not in agent_roles

    # IDs should be board-scoped
    agent_ids = [agent["id"] for agent in data]
    assert f"product_owner_{board_id}" in agent_ids


@pytest.mark.asyncio
async def test_get_agent_info(client: AsyncClient):
    """Test getting an agent's info."""
    board_id = await _get_default_board_id(client)
    response = await client.get(f"/api/agents/product_owner_{board_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Product Owner"
    assert data["type"] == "product_owner"
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
    board_id = await _get_default_board_id(client)
    response = await client.get(f"/api/agents/developer_{board_id}/status")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == f"developer_{board_id}"
    assert data["type"] == "developer"
    assert data["name"] == "Developer"
    assert data["status"] == "idle"
    assert data["current_task"] is None


@pytest.mark.asyncio
async def test_all_agents_have_valid_info(client: AsyncClient):
    """Test that all agents have valid info."""
    board_id = await _get_default_board_id(client)
    agent_roles = ["product_owner", "tech_lead", "developer", "code_reviewer", "qa", "scrum_master"]

    for role in agent_roles:
        agent_id = f"{role}_{board_id}"
        response = await client.get(f"/api/agents/{agent_id}")
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
