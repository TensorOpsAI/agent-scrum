"""
MCP Client for Agent Scrum Task Management.

This module provides a client that agents can use to interact with
the task management MCP server.
"""
import asyncio
import json
import logging
from typing import Any, Optional
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class TaskMCPClient:
    """Client for interacting with the Agent Scrum Tasks MCP server."""

    def __init__(self):
        self._session: Optional[ClientSession] = None
        self._read = None
        self._write = None

    async def connect(self) -> None:
        """Connect to the MCP server."""
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "app.mcp.task_server"],
        )
        self._read, self._write = await stdio_client(server_params).__aenter__()
        self._session = ClientSession(self._read, self._write)
        await self._session.__aenter__()
        await self._session.initialize()
        logger.info("Connected to Agent Scrum Tasks MCP server")

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self._session:
            await self._session.__aexit__(None, None, None)
        self._session = None
        self._read = None
        self._write = None
        logger.info("Disconnected from MCP server")

    async def list_tools(self) -> list[dict]:
        """List available tools from the server."""
        if not self._session:
            raise RuntimeError("Not connected to MCP server")

        result = await self._session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in result.tools
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict:
        """Call a tool on the MCP server.

        Args:
            name: The tool name
            arguments: Tool arguments

        Returns:
            The tool result as a dictionary
        """
        if not self._session:
            raise RuntimeError("Not connected to MCP server")

        result = await self._session.call_tool(name, arguments)

        # Parse the result
        if result.content and len(result.content) > 0:
            text = result.content[0].text
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"result": text}

        return {"result": None}

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    async def get_story(self, story_id: int) -> dict:
        """Get a story by ID."""
        return await self.call_tool("get_story", {"story_id": story_id})

    async def create_story(
        self,
        title: str,
        description: str,
        acceptance_criteria: str,
        priority: int = 1,
        prd_content: str = "",
    ) -> dict:
        """Create a new story."""
        return await self.call_tool("create_story", {
            "title": title,
            "description": description,
            "acceptance_criteria": acceptance_criteria,
            "priority": priority,
            "prd_content": prd_content,
        })

    async def update_story_status(self, story_id: int, new_status: str) -> dict:
        """Update a story's status."""
        return await self.call_tool("update_story_status", {
            "story_id": story_id,
            "new_status": new_status,
        })

    async def list_stories_by_status(self, status: str) -> list[dict]:
        """List stories by status."""
        return await self.call_tool("list_stories_by_status", {"status": status})

    async def get_task(self, task_id: int) -> dict:
        """Get a task by ID."""
        return await self.call_tool("get_task", {"task_id": task_id})

    async def get_tasks_for_story(self, story_id: int) -> list[dict]:
        """Get all tasks for a story."""
        return await self.call_tool("get_tasks_for_story", {"story_id": story_id})

    async def create_task(self, story_id: int, title: str, description: str) -> dict:
        """Create a new task."""
        return await self.call_tool("create_task", {
            "story_id": story_id,
            "title": title,
            "description": description,
        })

    async def update_task_status(self, task_id: int, new_status: str) -> dict:
        """Update a task's status."""
        return await self.call_tool("update_task_status", {
            "task_id": task_id,
            "new_status": new_status,
        })

    async def update_task_implementation(self, task_id: int, implementation_notes: str) -> dict:
        """Update task implementation notes."""
        return await self.call_tool("update_task_implementation", {
            "task_id": task_id,
            "implementation_notes": implementation_notes,
        })

    async def update_task_test_scenarios(self, task_id: int, test_scenarios: str) -> dict:
        """Update task test scenarios."""
        return await self.call_tool("update_task_test_scenarios", {
            "task_id": task_id,
            "test_scenarios": test_scenarios,
        })

    async def list_tasks_by_status(self, status: str) -> list[dict]:
        """List tasks by status."""
        return await self.call_tool("list_tasks_by_status", {"status": status})

    async def add_comment(
        self,
        content: str,
        agent_type: str,
        task_id: int = None,
        story_id: int = None,
    ) -> dict:
        """Add a comment to a task or story."""
        args = {"content": content, "agent_type": agent_type}
        if task_id:
            args["task_id"] = task_id
        if story_id:
            args["story_id"] = story_id
        return await self.call_tool("add_comment", args)

    async def get_task_comments(self, task_id: int) -> list[dict]:
        """Get comments for a task."""
        return await self.call_tool("get_task_comments", {"task_id": task_id})

    async def get_board_summary(self) -> dict:
        """Get the board summary."""
        return await self.call_tool("get_board_summary", {})


@asynccontextmanager
async def task_mcp_client():
    """Context manager for using the MCP client.

    Usage:
        async with task_mcp_client() as client:
            stories = await client.list_stories_by_status("ready_for_breakdown")
    """
    client = TaskMCPClient()
    try:
        await client.connect()
        yield client
    finally:
        await client.disconnect()


# Singleton client for reuse
_shared_client: Optional[TaskMCPClient] = None


async def get_shared_client() -> TaskMCPClient:
    """Get a shared MCP client instance.

    This client stays connected for the lifetime of the application.
    """
    global _shared_client
    if _shared_client is None:
        _shared_client = TaskMCPClient()
        await _shared_client.connect()
    return _shared_client


async def close_shared_client() -> None:
    """Close the shared MCP client."""
    global _shared_client
    if _shared_client is not None:
        await _shared_client.disconnect()
        _shared_client = None
