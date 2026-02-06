import json
from typing import Any
from fastapi import WebSocket
from dataclasses import dataclass, field
import asyncio


@dataclass
class ConnectionManager:
    active_connections: list[WebSocket] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, event: str, data: Any):
        message = json.dumps({"event": event, "data": data})
        async with self._lock:
            connections = list(self.active_connections)

        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception:
                await self.disconnect(connection)

    async def send_personal(self, websocket: WebSocket, event: str, data: Any):
        message = json.dumps({"event": event, "data": data})
        try:
            await websocket.send_text(message)
        except Exception:
            await self.disconnect(websocket)


# Singleton instance
manager = ConnectionManager()


# Event types
class WSEvents:
    STORY_CREATED = "story:created"
    STORY_UPDATED = "story:updated"
    STORY_DELETED = "story:deleted"
    TASK_CREATED = "task:created"
    TASK_UPDATED = "task:updated"
    TASK_DELETED = "task:deleted"
    COMMENT_ADDED = "comment:added"
    AGENT_STATUS_CHANGED = "agent:status_changed"
    AGENT_ACTIVITY = "agent:activity"
    AGENT_CHAT = "agent:chat"
    SWARM_STATUS = "swarm:status"
    BOARD_CREATED = "board:created"
    BOARD_DELETED = "board:deleted"


async def broadcast_story_created(story_data: dict):
    await manager.broadcast(WSEvents.STORY_CREATED, story_data)


async def broadcast_story_updated(story_data: dict):
    await manager.broadcast(WSEvents.STORY_UPDATED, story_data)


async def broadcast_story_deleted(story_id: int):
    await manager.broadcast(WSEvents.STORY_DELETED, {"id": story_id})


async def broadcast_task_created(task_data: dict):
    await manager.broadcast(WSEvents.TASK_CREATED, task_data)


async def broadcast_task_updated(task_data: dict):
    await manager.broadcast(WSEvents.TASK_UPDATED, task_data)


async def broadcast_task_deleted(task_id: int):
    await manager.broadcast(WSEvents.TASK_DELETED, {"id": task_id})


async def broadcast_comment_added(comment_data: dict):
    await manager.broadcast(WSEvents.COMMENT_ADDED, comment_data)


async def broadcast_agent_status(agent_type: str, status: str, current_task: str | None = None):
    await manager.broadcast(
        WSEvents.AGENT_STATUS_CHANGED,
        {"agent_type": agent_type, "status": status, "current_task": current_task}
    )


async def broadcast_agent_activity(agent_type: str, activity: str, details: dict | None = None):
    await manager.broadcast(
        WSEvents.AGENT_ACTIVITY,
        {"agent_type": agent_type, "activity": activity, "details": details or {}}
    )


async def broadcast_agent_chat(message_data: dict):
    """Broadcast a chat message from an agent."""
    await manager.broadcast(WSEvents.AGENT_CHAT, message_data)


async def broadcast_swarm_status(status: str):
    """Broadcast the swarm status (running, paused, stopped)."""
    await manager.broadcast(WSEvents.SWARM_STATUS, {"status": status})
