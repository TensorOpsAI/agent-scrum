"""
LangGraph Swarm - Multi-agent workflow using StateGraph.

This creates a workflow graph where:
1. Router checks board state and determines which agent should work
2. Agent nodes invoke LangGraph ReAct agents to do their work
3. Control returns to router for next assignment
"""
import asyncio
import random
from datetime import datetime, timedelta
from typing import Literal, Optional
from sqlalchemy import select
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from app.db.database import async_session_maker
from app.db.models import Story, Task, PipelineConfig, TaskStatus, DynamicAgent
from app.agents.langgraph_agents import get_agent
from app.agents.executor import set_swarm_active
from app.api.websocket.manager import broadcast_agent_status, broadcast_swarm_status
from app.a2a.router import a2a_router
from app.pipeline.templates import TEMPLATE_WORKFLOWS
from .state import SwarmState


# How long before an item is considered "stuck" (in seconds)
STUCK_THRESHOLD = 5

# Maximum iterations per cycle
MAX_ITERATIONS = 20

# Minimum working time for visual feedback (seconds)
MIN_WORKING_TIME = 3.0


async def get_active_agent_ids() -> set[str]:
    """Get the set of currently active agent IDs from the database."""
    async with async_session_maker() as db:
        result = await db.execute(
            select(DynamicAgent.id).where(DynamicAgent.is_active == True)
        )
        return set(result.scalars().all())


def is_stuck(updated_at: datetime) -> bool:
    """Check if an item is stuck based on last update time."""
    if updated_at is None:
        return True
    threshold = datetime.utcnow() - timedelta(seconds=STUCK_THRESHOLD)
    return updated_at < threshold


async def scan_board() -> dict:
    """Scan ALL boards with agent_automation enabled for items needing attention.

    Uses TEMPLATE_WORKFLOWS to determine which statuses have handlers
    instead of hardcoding software_dev statuses.

    Returns a dict with pending_stories and pending_tasks.
    """
    pending_stories = []
    pending_tasks = []

    async with async_session_maker() as db:
        # Find all boards with automation enabled
        board_result = await db.execute(
            select(PipelineConfig).where(PipelineConfig.agent_automation == True)
        )
        boards = board_result.scalars().all()

        if not boards:
            return {"pending_stories": [], "pending_tasks": []}

        for board in boards:
            workflow = TEMPLATE_WORKFLOWS.get(board.template_id, {})

            # Scan stories for statuses that have handlers
            for status_key, (agent_role, action) in workflow.get("story_handlers", {}).items():
                result = await db.execute(
                    select(Story).where(
                        Story.board_id == board.id,
                        Story.status == status_key,
                    )
                )
                for story in result.scalars().all():
                    if is_stuck(story.updated_at):
                        agent_id = f"{agent_role}_{board.id}"
                        pending_stories.append({
                            "id": story.id,
                            "board_id": story.board_id,
                            "title": story.title,
                            "status": story.status,
                            "action": action,
                            "agent": agent_id,
                            "message": f"Process story #{story.id}: {story.title}",
                        })

            # Scan tasks for statuses that have handlers
            for status_key, (agent_role, action) in workflow.get("task_handlers", {}).items():
                try:
                    task_status = TaskStatus(status_key)
                except ValueError:
                    continue

                result = await db.execute(
                    select(Task).join(Story, Task.story_id == Story.id).where(
                        Task.status == task_status,
                        Story.board_id == board.id,
                    )
                )
                for task in result.scalars().all():
                    if is_stuck(task.updated_at):
                        agent_id = f"{agent_role}_{board.id}"
                        pending_tasks.append({
                            "id": task.id,
                            "story_id": task.story_id,
                            "board_id": board.id,
                            "title": task.title,
                            "status": task.status.value,
                            "action": action,
                            "agent": agent_id,
                            "message": f"Process task #{task.id}: {task.title}",
                        })

    return {
        "pending_stories": pending_stories,
        "pending_tasks": pending_tasks,
    }


async def claim_item(item_type: str, item_id: int, expected_status: str) -> bool:
    """Claim an item by updating its timestamp to prevent double-processing."""
    async with async_session_maker() as db:
        if item_type == "story":
            result = await db.execute(select(Story).where(Story.id == item_id))
            item = result.scalar_one_or_none()
            if not item or str(item.status) != expected_status:
                return False
        else:
            result = await db.execute(select(Task).where(Task.id == item_id))
            item = result.scalar_one_or_none()
            if not item or item.status.value != expected_status:
                return False

        if not is_stuck(item.updated_at):
            return False

        item.updated_at = datetime.utcnow()
        await db.commit()
        return True


# Track which agents are currently working
_working_agents: dict[str, str] = {}  # agent_id -> work_key


async def router_node(state: SwarmState) -> SwarmState:
    """Router node - scans board and determines which agent should work next."""
    # Scan the board
    board = await scan_board()

    # Get currently active agents from database
    active_agents = await get_active_agent_ids()

    # Combine all pending work
    all_work = []
    for story in board["pending_stories"]:
        all_work.append(("story", story))
    for task in board["pending_tasks"]:
        all_work.append(("task", task))

    # Find available work
    next_agent = None
    next_work = None

    for work_type, work_item in all_work:
        agent_id = work_item["agent"]

        # Build work key
        work_key = f"{work_item['action']}:{work_item['id']}"

        # Check if agent is active in database
        if agent_id not in active_agents:
            continue

        # Check if agent is already working
        if agent_id in _working_agents:
            continue

        next_agent = agent_id
        next_work = {
            "type": work_type,
            "item": work_item,
            "work_key": work_key,
        }
        break

    return {
        **state,
        "pending_stories": board["pending_stories"],
        "pending_tasks": board["pending_tasks"],
        "active_agent": next_agent,
        "last_action": next_work,
        "iteration": state.get("iteration", 0) + 1,
    }


async def invoke_agent(agent_id: str, message: str, work_key: str, context: dict = None) -> dict:
    """Invoke a LangGraph agent via A2A router to record messages in chat.

    Args:
        agent_id: The agent to invoke
        message: The message/task for the agent
        work_key: Unique key for this work item
        context: Optional context (story_id, task_id, etc.)
    """
    global _working_agents

    # Mark agent as working
    _working_agents[agent_id] = work_key
    await broadcast_agent_status(agent_id, "working", message[:50])

    start_time = datetime.utcnow()

    try:
        # Use A2A router to send message - this records in chat
        async with async_session_maker() as db:
            result_task = await a2a_router.send_to_agent(
                from_agent="scrum_master",  # Swarm acts as scrum master
                to_agent=agent_id,
                message=message,
                context=context or {},
                db=db,
            )

        # Ensure minimum working time for visual feedback
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        if elapsed < MIN_WORKING_TIME:
            await asyncio.sleep(MIN_WORKING_TIME - elapsed)

        return {"success": True, "result": result_task}

    except Exception as e:
        print(f"[Swarm] Agent {agent_id} error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

    finally:
        # Mark agent as idle
        _working_agents.pop(agent_id, None)
        await broadcast_agent_status(agent_id, "idle", None)


async def dynamic_agent_node(state: SwarmState) -> SwarmState:
    """Universal agent node - handles all agents (both built-in and domain-specific)."""
    work = state.get("last_action")
    if not work:
        return {**state, "active_agent": None}

    agent_id = state.get("active_agent")
    item = work["item"]
    work_key = work["work_key"]

    # Claim the item
    item_type = work["type"]
    claimed = await claim_item(item_type, item["id"], item["status"])
    if not claimed:
        return {**state, "active_agent": None}

    # Build context for chat
    context = {"action": item.get("action", "work")}
    if item_type == "story":
        context["story_id"] = item["id"]
        context["board_id"] = item.get("board_id")
    else:
        context["task_id"] = item["id"]
        context["story_id"] = item.get("story_id")
        context["board_id"] = item.get("board_id")

    # Invoke the agent via A2A
    result = await invoke_agent(agent_id, item["message"], work_key, context)

    if result.get("success"):
        print(f"[Swarm] {agent_id} completed: {work_key}")
    else:
        print(f"[Swarm] {agent_id} failed: {result.get('error')}")

    return {**state, "active_agent": None}


def should_continue(state: SwarmState) -> Literal["router", "end"]:
    """Determine if the swarm should continue processing."""
    # Stop if max iterations reached
    if state.get("iteration", 0) >= MAX_ITERATIONS:
        return "end"

    # Stop if no more work
    if not state.get("pending_stories") and not state.get("pending_tasks"):
        return "end"

    return "router"


def route_to_agent(state: SwarmState) -> str:
    """Route to the agent node or end."""
    active = state.get("active_agent")
    if not active:
        return "end"
    return "agent"


def create_agent_swarm() -> StateGraph:
    """Create the multi-agent swarm graph.

    Returns a compiled StateGraph that orchestrates all agents.
    All agents (built-in and domain-specific) route through the
    single dynamic_agent_node.
    """
    workflow = StateGraph(SwarmState)

    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("agent", dynamic_agent_node)

    # Set entry point
    workflow.set_entry_point("router")

    # Add conditional routing from router to agent
    workflow.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "agent": "agent",
            "end": END,
        }
    )

    # After agent, check if we should continue
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "router": "router",
            "end": END,
        }
    )

    return workflow


class ScrumSwarm:
    """High-level interface for the Scrum agent swarm."""

    def __init__(self):
        self._graph = None
        self._compiled = None
        self._running = False
        self._paused = False
        self._task: Optional[asyncio.Task] = None

    @property
    def is_running(self) -> bool:
        """Check if the swarm is running."""
        return self._running and not self._paused

    @property
    def status(self) -> str:
        """Get the current swarm status."""
        if not self._running:
            return "stopped"
        if self._paused:
            return "paused"
        return "running"

    def _ensure_compiled(self):
        """Ensure the graph is compiled."""
        if self._compiled is None:
            self._graph = create_agent_swarm()
            self._compiled = self._graph.compile()

    async def run_once(self) -> dict:
        """Run one iteration of the swarm."""
        self._ensure_compiled()

        initial_state: SwarmState = {
            "messages": [],
            "active_agent": None,
            "pending_stories": [],
            "pending_tasks": [],
            "current_work": {},
            "last_action": None,
            "iteration": 0,
        }

        result = await self._compiled.ainvoke(initial_state)
        return result

    async def start(self):
        """Start the background monitoring loop."""
        if self._running:
            # If already running but paused, unpause
            if self._paused:
                self._paused = False
                set_swarm_active(True)
                await broadcast_swarm_status("running")
                print("[Swarm] Agent swarm resumed")
            return
        self._running = True
        self._paused = False
        set_swarm_active(True)
        self._task = asyncio.create_task(self._monitor_loop())
        await broadcast_swarm_status("running")
        print("[Swarm] Agent swarm started")

    async def stop(self):
        """Stop the background monitoring loop completely."""
        self._running = False
        self._paused = False
        set_swarm_active(False)
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        # Clear working agents
        _working_agents.clear()
        await broadcast_swarm_status("stopped")
        print("[Swarm] Agent swarm stopped")

    async def pause(self):
        """Pause the swarm (agents stop taking new work)."""
        if self._running and not self._paused:
            self._paused = True
            set_swarm_active(False)
            await broadcast_swarm_status("paused")
            print("[Swarm] Agent swarm paused")

    async def resume(self):
        """Resume the swarm after pausing."""
        if self._running and self._paused:
            self._paused = False
            set_swarm_active(True)
            await broadcast_swarm_status("running")
            print("[Swarm] Agent swarm resumed")

    async def _monitor_loop(self):
        """Main monitoring loop."""
        # Initial delay to let app start up
        await asyncio.sleep(3)

        while self._running:
            try:
                # Only run if not paused
                if not self._paused:
                    await self.run_once()
            except Exception as e:
                print(f"[Swarm] Error: {e}")
                import traceback
                traceback.print_exc()

            # Random interval for natural behavior
            interval = random.uniform(3, 6)
            await asyncio.sleep(interval)


# Global swarm instance
swarm = ScrumSwarm()
