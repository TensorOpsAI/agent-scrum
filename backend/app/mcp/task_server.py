"""
MCP Server for Agent Scrum Task Management.

This MCP server exposes the story/task management tools so that agents
can interact with the scrum board through the Model Context Protocol.

Run with: python -m app.mcp.task_server
Or use as a library in your agent system.
"""
import asyncio
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from sqlalchemy import select

# Import models and db
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.session import get_current_session_maker
from app.db.models import Story, Task, Comment, PipelineConfig
from app.pipeline.templates import get_valid_statuses
from sqlalchemy.orm import selectinload

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the MCP server
server = Server("agent-scrum-tasks")


# ============================================================================
# Tool Definitions
# ============================================================================

TOOLS = [
    Tool(
        name="get_story",
        description="Fetch a story by ID with its details including title, description, acceptance criteria, status, and priority.",
        inputSchema={
            "type": "object",
            "properties": {
                "story_id": {
                    "type": "integer",
                    "description": "The ID of the story to fetch"
                }
            },
            "required": ["story_id"]
        }
    ),
    Tool(
        name="create_story",
        description="Create a new user story on a board.",
        inputSchema={
            "type": "object",
            "properties": {
                "board_id": {
                    "type": "integer",
                    "description": "The ID of the board to create the story on"
                },
                "title": {
                    "type": "string",
                    "description": "The story title (e.g., 'As a user, I want...')"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of the story"
                },
                "acceptance_criteria": {
                    "type": "string",
                    "description": "List of acceptance criteria"
                },
                "priority": {
                    "type": "integer",
                    "description": "Priority level (1=highest)",
                    "default": 1
                },
                "prd_content": {
                    "type": "string",
                    "description": "Original PRD content if applicable",
                    "default": ""
                }
            },
            "required": ["board_id", "title", "description", "acceptance_criteria"]
        }
    ),
    Tool(
        name="update_story_status",
        description="Update a story's status. Valid statuses depend on the active pipeline configuration.",
        inputSchema={
            "type": "object",
            "properties": {
                "story_id": {
                    "type": "integer",
                    "description": "The ID of the story to update"
                },
                "new_status": {
                    "type": "string",
                    "description": "The new status (must be a valid column key in the active pipeline)"
                }
            },
            "required": ["story_id", "new_status"]
        }
    ),
    Tool(
        name="list_stories_by_status",
        description="List all stories with a specific status.",
        inputSchema={
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "The status to filter by"
                }
            },
            "required": ["status"]
        }
    ),
    Tool(
        name="get_task",
        description="Fetch a task by ID with its details including title, description, implementation notes, test scenarios, and status.",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "The ID of the task to fetch"
                }
            },
            "required": ["task_id"]
        }
    ),
    Tool(
        name="get_tasks_for_story",
        description="Get all tasks for a specific story.",
        inputSchema={
            "type": "object",
            "properties": {
                "story_id": {
                    "type": "integer",
                    "description": "The ID of the story"
                }
            },
            "required": ["story_id"]
        }
    ),
    Tool(
        name="create_task",
        description="Create a new task for a story. Tasks are created in 'draft' status.",
        inputSchema={
            "type": "object",
            "properties": {
                "story_id": {
                    "type": "integer",
                    "description": "The ID of the story this task belongs to"
                },
                "title": {
                    "type": "string",
                    "description": "The task title"
                },
                "description": {
                    "type": "string",
                    "description": "The task description"
                }
            },
            "required": ["story_id", "title", "description"]
        }
    ),
    Tool(
        name="update_task_status",
        description="Update a task's status. Valid statuses: draft, pending_review, in_review, ready_for_development, in_progress, code_review, code_review_in_progress, ready_for_qa, qa_in_progress, done",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "The ID of the task to update"
                },
                "new_status": {
                    "type": "string",
                    "description": "The new status",
                    "enum": ["draft", "pending_review", "in_review", "ready_for_development", "in_progress", "code_review", "code_review_in_progress", "ready_for_qa", "qa_in_progress", "done"]
                }
            },
            "required": ["task_id", "new_status"]
        }
    ),
    Tool(
        name="update_task_implementation",
        description="Update a task's implementation notes.",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "The ID of the task to update"
                },
                "implementation_notes": {
                    "type": "string",
                    "description": "The implementation notes/approach"
                }
            },
            "required": ["task_id", "implementation_notes"]
        }
    ),
    Tool(
        name="update_task_test_scenarios",
        description="Update a task's test scenarios.",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "The ID of the task to update"
                },
                "test_scenarios": {
                    "type": "string",
                    "description": "The test scenarios"
                }
            },
            "required": ["task_id", "test_scenarios"]
        }
    ),
    Tool(
        name="list_tasks_by_status",
        description="List all tasks with a specific status.",
        inputSchema={
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "The status to filter by",
                    "enum": ["draft", "pending_review", "in_review", "ready_for_development", "in_progress", "code_review", "code_review_in_progress", "ready_for_qa", "qa_in_progress", "done"]
                }
            },
            "required": ["status"]
        }
    ),
    Tool(
        name="add_comment",
        description="Add a comment to a task or story.",
        inputSchema={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The comment content"
                },
                "agent_type": {
                    "type": "string",
                    "description": "The type of agent adding the comment",
                    "enum": ["product_owner", "tech_lead", "developer", "code_reviewer", "qa", "scrum_master", "client"]
                },
                "task_id": {
                    "type": "integer",
                    "description": "Optional task ID (if commenting on a task)"
                },
                "story_id": {
                    "type": "integer",
                    "description": "Optional story ID (if commenting on a story)"
                }
            },
            "required": ["content", "agent_type"]
        }
    ),
    Tool(
        name="get_task_comments",
        description="Get all comments for a task.",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "The ID of the task"
                }
            },
            "required": ["task_id"]
        }
    ),
    Tool(
        name="get_board_summary",
        description="Get a summary of the current board state - counts of stories and tasks in each status.",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
]


# ============================================================================
# Tool Implementations
# ============================================================================

async def get_story(story_id: int) -> dict:
    """Fetch a story by ID."""
    async with get_current_session_maker()() as db:
        result = await db.execute(select(Story).where(Story.id == story_id))
        story = result.scalar_one_or_none()

        if not story:
            return {"error": f"Story {story_id} not found"}

        return {
            "id": story.id,
            "title": story.title,
            "description": story.description,
            "acceptance_criteria": story.acceptance_criteria,
            "status": story.status,
            "priority": story.priority,
            "prd_content": story.prd_content,
        }


async def create_story(
    board_id: int,
    title: str,
    description: str,
    acceptance_criteria: str,
    priority: int = 1,
    prd_content: str = "",
) -> dict:
    """Create a new story on a board."""
    async with get_current_session_maker()() as db:
        board_result = await db.execute(
            select(PipelineConfig).where(PipelineConfig.id == board_id)
        )
        board = board_result.scalar_one_or_none()
        if not board:
            return {"error": f"Board {board_id} not found"}

        first_status = board.columns[0]["key"]

        story = Story(
            board_id=board_id,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            priority=priority,
            prd_content=prd_content,
            status=first_status,
        )
        db.add(story)
        await db.commit()
        await db.refresh(story)

        return {
            "id": story.id,
            "board_id": story.board_id,
            "title": story.title,
            "description": story.description,
            "acceptance_criteria": story.acceptance_criteria,
            "status": story.status,
            "priority": story.priority,
        }


async def update_story_status(story_id: int, new_status: str) -> dict:
    """Update a story's status."""
    async with get_current_session_maker()() as db:
        result = await db.execute(
            select(Story).where(Story.id == story_id).options(selectinload(Story.board))
        )
        story = result.scalar_one_or_none()

        if not story:
            return {"error": f"Story {story_id} not found"}

        # Validate against story's board columns
        board_config = {"columns": story.board.columns}
        valid = get_valid_statuses(board_config)
        if new_status not in valid:
            return {"error": f"Invalid status: {new_status}. Valid: {valid}"}

        story.status = new_status
        await db.commit()
        return {"success": True, "message": f"Story {story_id} status updated to {new_status}"}


async def list_stories_by_status(status: str) -> list[dict]:
    """List stories by status."""
    async with get_current_session_maker()() as db:
        result = await db.execute(select(Story).where(Story.status == status))
        stories = result.scalars().all()

        return [
            {
                "id": s.id,
                "title": s.title,
                "status": s.status,
                "priority": s.priority,
            }
            for s in stories
        ]


async def get_task(task_id: int) -> dict:
    """Fetch a task by ID."""
    async with get_current_session_maker()() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            return {"error": f"Task {task_id} not found"}

        return {
            "id": task.id,
            "story_id": task.story_id,
            "title": task.title,
            "description": task.description,
            "implementation_notes": task.implementation_notes,
            "test_scenarios": task.test_scenarios,
            "status": task.status,
            "assigned_agent": task.assigned_agent,
        }


async def get_tasks_for_story(story_id: int) -> list[dict]:
    """Get all tasks for a story."""
    async with get_current_session_maker()() as db:
        result = await db.execute(select(Task).where(Task.story_id == story_id))
        tasks = result.scalars().all()

        return [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "implementation_notes": t.implementation_notes,
                "test_scenarios": t.test_scenarios,
            }
            for t in tasks
        ]


async def create_task(story_id: int, title: str, description: str) -> dict:
    """Create a new task."""
    async with get_current_session_maker()() as db:
        task = Task(
            story_id=story_id,
            title=title,
            description=description,
            status="draft",
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        return {
            "id": task.id,
            "story_id": task.story_id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
        }


async def update_task_status(task_id: int, new_status: str) -> dict:
    """Update a task's status."""
    async with get_current_session_maker()() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            return {"error": f"Task {task_id} not found"}

        task.status = new_status
        await db.commit()
        return {"success": True, "message": f"Task {task_id} status updated to {new_status}"}


async def update_task_implementation(task_id: int, implementation_notes: str) -> dict:
    """Update task implementation notes."""
    async with get_current_session_maker()() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            return {"error": f"Task {task_id} not found"}

        task.implementation_notes = implementation_notes
        await db.commit()
        return {"success": True, "message": f"Task {task_id} implementation notes updated"}


async def update_task_test_scenarios(task_id: int, test_scenarios: str) -> dict:
    """Update task test scenarios."""
    async with get_current_session_maker()() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            return {"error": f"Task {task_id} not found"}

        task.test_scenarios = test_scenarios
        await db.commit()
        return {"success": True, "message": f"Task {task_id} test scenarios updated"}


async def list_tasks_by_status(status: str) -> list[dict]:
    """List tasks by status."""
    async with get_current_session_maker()() as db:
        result = await db.execute(select(Task).where(Task.status == status))
        tasks = result.scalars().all()

        return [
            {
                "id": t.id,
                "story_id": t.story_id,
                "title": t.title,
                "status": t.status,
            }
            for t in tasks
        ]


async def add_comment(
    content: str,
    agent_type: str,
    task_id: int = None,
    story_id: int = None,
) -> dict:
    """Add a comment to a task or story."""
    async with get_current_session_maker()() as db:
        comment = Comment(
            content=content,
            agent_type=agent_type,
            task_id=task_id,
            story_id=story_id,
        )
        db.add(comment)
        await db.commit()
        await db.refresh(comment)

        return {
            "id": comment.id,
            "content": comment.content,
            "agent_type": comment.agent_type,
            "task_id": comment.task_id,
            "story_id": comment.story_id,
        }


async def get_task_comments(task_id: int) -> list[dict]:
    """Get all comments for a task."""
    async with get_current_session_maker()() as db:
        result = await db.execute(
            select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at)
        )
        comments = result.scalars().all()

        return [
            {
                "id": c.id,
                "content": c.content,
                "agent_type": c.agent_type,
                "created_at": c.created_at.isoformat(),
            }
            for c in comments
        ]


async def get_board_summary() -> dict:
    """Get a summary of all boards."""
    async with get_current_session_maker()() as db:
        from sqlalchemy import func

        # Get all boards
        boards_result = await db.execute(select(PipelineConfig))
        boards = boards_result.scalars().all()

        board_summaries = []
        for board in boards:
            story_count_result = await db.execute(
                select(func.count(Story.id)).where(Story.board_id == board.id)
            )
            story_count = story_count_result.scalar() or 0
            board_summaries.append({
                "id": board.id,
                "name": board.name,
                "template_id": board.template_id,
                "story_count": story_count,
            })

        # Count tasks by status (across all boards)
        _all_statuses = ["draft", "pending_review", "ready_for_development", "in_progress", "code_review", "ready_for_qa", "qa_in_progress", "done", "pending", "scheduled", "review", "identified", "verified"]
        task_counts = {}
        for status in _all_statuses:
            result = await db.execute(
                select(func.count(Task.id)).where(Task.status == status)
            )
            count = result.scalar() or 0
            if count > 0:
                task_counts[status] = count

        return {
            "boards": board_summaries,
            "tasks": task_counts,
            "total_tasks": sum(task_counts.values()),
        }


# ============================================================================
# MCP Server Handlers
# ============================================================================

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return TOOLS


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    logger.info(f"Tool called: {name} with args: {arguments}")

    try:
        # Route to the appropriate function
        if name == "get_story":
            result = await get_story(arguments["story_id"])
        elif name == "create_story":
            result = await create_story(
                board_id=arguments["board_id"],
                title=arguments["title"],
                description=arguments["description"],
                acceptance_criteria=arguments["acceptance_criteria"],
                priority=arguments.get("priority", 1),
                prd_content=arguments.get("prd_content", ""),
            )
        elif name == "update_story_status":
            result = await update_story_status(arguments["story_id"], arguments["new_status"])
        elif name == "list_stories_by_status":
            result = await list_stories_by_status(arguments["status"])
        elif name == "get_task":
            result = await get_task(arguments["task_id"])
        elif name == "get_tasks_for_story":
            result = await get_tasks_for_story(arguments["story_id"])
        elif name == "create_task":
            result = await create_task(
                story_id=arguments["story_id"],
                title=arguments["title"],
                description=arguments["description"],
            )
        elif name == "update_task_status":
            result = await update_task_status(arguments["task_id"], arguments["new_status"])
        elif name == "update_task_implementation":
            result = await update_task_implementation(
                arguments["task_id"],
                arguments["implementation_notes"],
            )
        elif name == "update_task_test_scenarios":
            result = await update_task_test_scenarios(
                arguments["task_id"],
                arguments["test_scenarios"],
            )
        elif name == "list_tasks_by_status":
            result = await list_tasks_by_status(arguments["status"])
        elif name == "add_comment":
            result = await add_comment(
                content=arguments["content"],
                agent_type=arguments["agent_type"],
                task_id=arguments.get("task_id"),
                story_id=arguments.get("story_id"),
            )
        elif name == "get_task_comments":
            result = await get_task_comments(arguments["task_id"])
        elif name == "get_board_summary":
            result = await get_board_summary()
        else:
            result = {"error": f"Unknown tool: {name}"}

        import json
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}", exc_info=True)
        import json
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Run the MCP server."""
    logger.info("MCP server starting (requires session context)")

    # Run the server
    logger.info("Starting Agent Scrum Tasks MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
