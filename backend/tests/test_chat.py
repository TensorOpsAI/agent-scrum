import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import AgentMessage
from app.agents.chat import send_chat_message, ChatTemplates


@pytest.mark.asyncio
async def test_get_chat_messages_empty(client: AsyncClient):
    """Test getting chat messages when none exist."""
    response = await client.get("/api/chat")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_chat_messages_with_data(client: AsyncClient, test_session: AsyncSession):
    """Test getting chat messages after creating some."""
    # Create test messages directly in DB (agent IDs are now strings)
    msg1 = AgentMessage(
        from_agent="product_owner",
        to_agent="developer",
        content="Hey team, I've created a new story!",
        story_id=1,
        message_type="announcement",
    )
    msg2 = AgentMessage(
        from_agent="developer",
        to_agent="tech_lead",
        content="@Tech Lead, I've broken down the story into tasks. PTAL!",
        story_id=1,
        message_type="handoff",
    )
    test_session.add(msg1)
    test_session.add(msg2)
    await test_session.commit()

    response = await client.get("/api/chat")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2

    # Check messages exist (order may vary based on DB)
    from_agents = {d["from_agent"] for d in data}
    assert "product_owner" in from_agents
    assert "developer" in from_agents

    # Find and check specific messages
    po_msg = next(d for d in data if d["from_agent"] == "product_owner")
    assert po_msg["from_agent_name"] == "Product Owner"
    assert po_msg["to_agent"] == "developer"
    assert po_msg["content"] == "Hey team, I've created a new story!"

    dev_msg = next(d for d in data if d["from_agent"] == "developer")
    assert dev_msg["to_agent"] == "tech_lead"


@pytest.mark.asyncio
async def test_get_chat_messages_limit(client: AsyncClient, test_session: AsyncSession):
    """Test chat message limit parameter."""
    # Create 10 messages
    for i in range(10):
        msg = AgentMessage(
            from_agent="developer",
            content=f"Message {i}",
            message_type="chat",
        )
        test_session.add(msg)
    await test_session.commit()

    # Get with limit
    response = await client.get("/api/chat?limit=5")
    assert response.status_code == 200
    assert len(response.json()) == 5


@pytest.mark.asyncio
async def test_chat_message_without_recipient(client: AsyncClient, test_session: AsyncSession):
    """Test chat message broadcast (no specific recipient)."""
    msg = AgentMessage(
        from_agent="qa",
        to_agent=None,
        content="All tests passed!",
        task_id=42,
        message_type="announcement",
    )
    test_session.add(msg)
    await test_session.commit()

    response = await client.get("/api/chat")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["to_agent"] is None
    assert data[0]["to_agent_name"] is None
    assert data[0]["task_id"] == 42


@pytest.mark.asyncio
async def test_send_chat_message_persists(client: AsyncClient, test_session: AsyncSession):
    """Test that send_chat_message commits messages to the database."""
    # Use the send_chat_message function (which should commit)
    message = await send_chat_message(
        from_agent="product_owner",
        content="Test message from send_chat_message",
        db=test_session,
        to_agent="developer",
        story_id=1,
        message_type="test",
    )

    # Verify message was created
    assert message.id is not None

    # Fetch messages via API to verify persistence
    response = await client.get("/api/chat")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "Test message from send_chat_message"
    assert data[0]["from_agent"] == "product_owner"
    assert data[0]["to_agent"] == "developer"


@pytest.mark.asyncio
async def test_chat_templates():
    """Test chat message templates produce expected content."""
    # Test PRD received
    msg = ChatTemplates.prd_received(3)
    assert "3" in msg
    assert "stories" in msg

    # Test breakdown complete
    msg = ChatTemplates.breakdown_complete(1, 5)
    assert "STORY-1" in msg
    assert "5 tasks" in msg
    assert "@Tech Lead" in msg

    # Test implementation done
    msg = ChatTemplates.implementation_done(42)
    assert "TASK-42" in msg
    assert "@Code Reviewer" in msg

    # Test QA passed
    msg = ChatTemplates.qa_passed(99)
    assert "TASK-99" in msg
    assert "passed" in msg
