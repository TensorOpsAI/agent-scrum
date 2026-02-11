import json
from typing import Any
from fastapi import WebSocket
from dataclasses import dataclass, field
import asyncio


def _get_session_id() -> str:
    """Get session_id from contextvar, fallback to 'global'."""
    try:
        from app.session import get_current_session
        return get_current_session().id
    except LookupError:
        return "global"


@dataclass
class ConnectionManager:
    _rooms: dict[str, list[WebSocket]] = field(default_factory=dict)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def connect(self, websocket: WebSocket, session_id: str = "global"):
        await websocket.accept()
        async with self._lock:
            if session_id not in self._rooms:
                self._rooms[session_id] = []
            self._rooms[session_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, session_id: str = "global"):
        async with self._lock:
            if session_id in self._rooms:
                if websocket in self._rooms[session_id]:
                    self._rooms[session_id].remove(websocket)
                if not self._rooms[session_id]:
                    del self._rooms[session_id]

    async def broadcast(self, event: str, data: Any, session_id: str | None = None):
        if session_id is None:
            session_id = _get_session_id()
        message = json.dumps({"event": event, "data": data})
        async with self._lock:
            connections = list(self._rooms.get(session_id, []))

        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception:
                await self.disconnect(connection, session_id)

    async def send_personal(self, websocket: WebSocket, event: str, data: Any):
        message = json.dumps({"event": event, "data": data})
        try:
            await websocket.send_text(message)
        except Exception:
            pass

    async def remove_session(self, session_id: str):
        """Remove all connections for a session."""
        async with self._lock:
            connections = self._rooms.pop(session_id, [])
        for ws in connections:
            try:
                await ws.close()
            except Exception:
                pass


# Singleton instance (routes by room)
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
