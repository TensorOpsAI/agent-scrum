import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_agents(client: AsyncClient):
    """Test listing all registered agents (only active ones)."""
    response = await client.get("/api/agents")
    assert response.status_code == 200

    data = response.json()
    # Only 5 active agents by default (scrum_master is inactive)
    assert len(data) == 5  # product_owner, tech_lead, developer, code_reviewer, qa

    agent_types = [agent["type"] for agent in data]
    assert "product_owner" in agent_types
    assert "tech_lead" in agent_types
    assert "developer" in agent_types
    assert "code_reviewer" in agent_types
    assert "qa" in agent_types
    # scrum_master is inactive by default
    assert "scrum_master" not in agent_types


@pytest.mark.asyncio
async def test_get_agent_info(client: AsyncClient):
    """Test getting an agent's info."""
    response = await client.get("/api/agents/product_owner")
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Product Owner"
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
    response = await client.get("/api/agents/developer/status")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == "developer"
    assert data["type"] == "developer"
    assert data["name"] == "Developer"
    assert data["status"] == "idle"
    assert data["current_task"] is None


@pytest.mark.asyncio
async def test_all_agents_have_valid_info(client: AsyncClient):
    """Test that all agents have valid info."""
    agent_types = ["product_owner", "tech_lead", "developer", "code_reviewer", "qa", "scrum_master"]

    for agent_type in agent_types:
        response = await client.get(f"/api/agents/{agent_type}")
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
