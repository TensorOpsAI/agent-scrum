import pytest
from app.a2a.protocol import A2AProtocolHandler
from app.schemas.a2a import (
    A2ATask,
    A2ATaskState,
    Message,
    TextPart,
    A2AErrorCodes,
)


@pytest.fixture
def protocol_handler():
    """Create a fresh protocol handler for each test."""
    return A2AProtocolHandler()


@pytest.mark.asyncio
async def test_task_send_creates_new_task(protocol_handler):
    """Test that tasks/send creates a new task if it doesn't exist."""
    request = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tasks/send",
        "params": {
            "id": "test-task-1",
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": "Hello agent"}]
            }
        }
    }

    response = await protocol_handler.handle_request(request)

    assert response.error is None
    assert response.result is not None
    assert response.result["id"] == "test-task-1"
    assert response.result["state"] == "submitted"
    assert len(response.result["messages"]) == 1


@pytest.mark.asyncio
async def test_task_send_continues_existing_task(protocol_handler):
    """Test that tasks/send adds to an existing task."""
    # Send first message
    request1 = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tasks/send",
        "params": {
            "id": "test-task-1",
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": "First message"}]
            }
        }
    }
    await protocol_handler.handle_request(request1)

    # Send second message
    request2 = {
        "jsonrpc": "2.0",
        "id": "2",
        "method": "tasks/send",
        "params": {
            "id": "test-task-1",
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": "Second message"}]
            }
        }
    }
    response = await protocol_handler.handle_request(request2)

    assert response.error is None
    assert len(response.result["messages"]) == 2


@pytest.mark.asyncio
async def test_task_get_existing(protocol_handler):
    """Test getting an existing task."""
    # Create a task first
    send_request = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tasks/send",
        "params": {
            "id": "test-task-1",
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": "Hello"}]
            }
        }
    }
    await protocol_handler.handle_request(send_request)

    # Get the task
    get_request = {
        "jsonrpc": "2.0",
        "id": "2",
        "method": "tasks/get",
        "params": {"id": "test-task-1"}
    }
    response = await protocol_handler.handle_request(get_request)

    assert response.error is None
    assert response.result["id"] == "test-task-1"


@pytest.mark.asyncio
async def test_task_get_not_found(protocol_handler):
    """Test getting a non-existent task."""
    request = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tasks/get",
        "params": {"id": "nonexistent-task"}
    }
    response = await protocol_handler.handle_request(request)

    assert response.error is not None
    assert response.error.code == A2AErrorCodes.TASK_NOT_FOUND


@pytest.mark.asyncio
async def test_task_cancel(protocol_handler):
    """Test canceling a task."""
    # Create a task first
    send_request = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tasks/send",
        "params": {
            "id": "test-task-1",
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": "Hello"}]
            }
        }
    }
    await protocol_handler.handle_request(send_request)

    # Cancel the task
    cancel_request = {
        "jsonrpc": "2.0",
        "id": "2",
        "method": "tasks/cancel",
        "params": {"id": "test-task-1"}
    }
    response = await protocol_handler.handle_request(cancel_request)

    assert response.error is None
    assert response.result["state"] == "canceled"


@pytest.mark.asyncio
async def test_invalid_method(protocol_handler):
    """Test calling an unknown method."""
    request = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "unknown/method",
        "params": {}
    }
    response = await protocol_handler.handle_request(request)

    assert response.error is not None
    assert response.error.code == A2AErrorCodes.METHOD_NOT_FOUND


@pytest.mark.asyncio
async def test_invalid_request_format(protocol_handler):
    """Test handling an invalid request format."""
    request = {"invalid": "format"}
    response = await protocol_handler.handle_request(request)

    assert response.error is not None
    assert response.error.code == A2AErrorCodes.PARSE_ERROR


@pytest.mark.asyncio
async def test_update_task_state(protocol_handler):
    """Test updating a task's state."""
    # Create a task
    send_request = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tasks/send",
        "params": {
            "id": "test-task-1",
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": "Hello"}]
            }
        }
    }
    await protocol_handler.handle_request(send_request)

    # Update state
    protocol_handler.update_task_state("test-task-1", A2ATaskState.WORKING)

    # Verify state changed
    task = protocol_handler.get_task("test-task-1")
    assert task.state == A2ATaskState.WORKING


@pytest.mark.asyncio
async def test_add_task_message(protocol_handler):
    """Test adding a message to a task."""
    # Create a task
    send_request = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tasks/send",
        "params": {
            "id": "test-task-1",
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": "Hello"}]
            }
        }
    }
    await protocol_handler.handle_request(send_request)

    # Add a message
    protocol_handler.add_task_message("test-task-1", "agent", "Response")

    # Verify message added
    task = protocol_handler.get_task("test-task-1")
    assert len(task.messages) == 2
    assert task.messages[1].role == "agent"
