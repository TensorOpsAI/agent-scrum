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
from app.db.models import Story, Task, StoryStatus, TaskStatus, DynamicAgent
from app.agents.langgraph_agents import get_agent
from app.api.websocket.manager import broadcast_agent_status, broadcast_swarm_status
from app.a2a.router import a2a_router
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
    """Scan the board for items needing attention.

    Returns a dict with pending_stories and pending_tasks.
    """
    pending_stories = []
    pending_tasks = []

    async with async_session_maker() as db:
        # Stories ready for breakdown
        result = await db.execute(
            select(Story).where(Story.status == StoryStatus.READY_FOR_BREAKDOWN)
        )
        for story in result.scalars().all():
            if is_stuck(story.updated_at):
                pending_stories.append({
                    "id": story.id,
                    "title": story.title,
                    "status": story.status.value,
                    "action": "breakdown",
                    "agent": "developer",
                    "message": f"Break down story #{story.id}: {story.title}",
                })

        # Stories with tasks in review
        result = await db.execute(
            select(Story).where(Story.status == StoryStatus.TASKS_IN_REVIEW)
        )
        for story in result.scalars().all():
            if is_stuck(story.updated_at):
                pending_stories.append({
                    "id": story.id,
                    "title": story.title,
                    "status": story.status.value,
                    "action": "review_tasks",
                    "agent": "tech_lead",
                    "message": f"Review tasks for story #{story.id}: {story.title}",
                })

        # Tasks ready for development
        result = await db.execute(
            select(Task).where(Task.status == TaskStatus.READY_FOR_DEVELOPMENT)
        )
        for task in result.scalars().all():
            if is_stuck(task.updated_at):
                pending_tasks.append({
                    "id": task.id,
                    "story_id": task.story_id,
                    "title": task.title,
                    "status": task.status.value,
                    "action": "implementation",
                    "agent": "developer",
                    "message": f"Write implementation notes for task #{task.id}: {task.title}",
                })

        # Tasks ready for code review
        result = await db.execute(
            select(Task).where(Task.status == TaskStatus.CODE_REVIEW)
        )
        for task in result.scalars().all():
            if is_stuck(task.updated_at):
                pending_tasks.append({
                    "id": task.id,
                    "story_id": task.story_id,
                    "title": task.title,
                    "status": task.status.value,
                    "action": "code_review",
                    "agent": "code_reviewer",
                    "message": f"Review implementation for task #{task.id}: {task.title}",
                })

        # Tasks ready for QA
        result = await db.execute(
            select(Task).where(Task.status == TaskStatus.READY_FOR_QA)
        )
        for task in result.scalars().all():
            if is_stuck(task.updated_at):
                pending_tasks.append({
                    "id": task.id,
                    "story_id": task.story_id,
                    "title": task.title,
                    "status": task.status.value,
                    "action": "qa_scenarios",
                    "agent": "qa",
                    "message": f"Create test scenarios for task #{task.id}: {task.title}",
                })

        # Tasks in QA progress
        result = await db.execute(
            select(Task).where(Task.status == TaskStatus.QA_IN_PROGRESS)
        )
        for task in result.scalars().all():
            if is_stuck(task.updated_at):
                pending_tasks.append({
                    "id": task.id,
                    "story_id": task.story_id,
                    "title": task.title,
                    "status": task.status.value,
                    "action": "qa_run",
                    "agent": "qa",
                    "message": f"Run tests for task #{task.id}: {task.title}",
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
            if not item or item.status.value != expected_status:
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


async def developer_node(state: SwarmState) -> SwarmState:
    """Developer agent node."""
    work = state.get("last_action")
    if not work:
        return {**state, "active_agent": None}

    item = work["item"]
    work_key = work["work_key"]

    # Claim the item
    item_type = work["type"]
    claimed = await claim_item(item_type, item["id"], item["status"])
    if not claimed:
        return {**state, "active_agent": None}

    # Build context for chat
    context = {"action": item["action"]}
    if item_type == "story":
        context["story_id"] = item["id"]
    else:
        context["task_id"] = item["id"]
        context["story_id"] = item.get("story_id")

    # Invoke the agent via A2A
    result = await invoke_agent("developer", item["message"], work_key, context)

    if result.get("success"):
        print(f"[Swarm] Developer completed: {work_key}")
    else:
        print(f"[Swarm] Developer failed: {result.get('error')}")

    return {**state, "active_agent": None}


async def tech_lead_node(state: SwarmState) -> SwarmState:
    """Tech Lead agent node."""
    work = state.get("last_action")
    if not work:
        return {**state, "active_agent": None}

    item = work["item"]
    work_key = work["work_key"]

    # Claim the item
    claimed = await claim_item("story", item["id"], item["status"])
    if not claimed:
        return {**state, "active_agent": None}

    # Build context for chat
    context = {"action": item["action"], "story_id": item["id"]}

    # Invoke the agent via A2A
    result = await invoke_agent("tech_lead", item["message"], work_key, context)

    if result.get("success"):
        print(f"[Swarm] Tech Lead completed: {work_key}")
    else:
        print(f"[Swarm] Tech Lead failed: {result.get('error')}")

    return {**state, "active_agent": None}


async def code_reviewer_node(state: SwarmState) -> SwarmState:
    """Code Reviewer agent node."""
    work = state.get("last_action")
    if not work:
        return {**state, "active_agent": None}

    item = work["item"]
    work_key = work["work_key"]

    # Claim the item
    claimed = await claim_item("task", item["id"], item["status"])
    if not claimed:
        return {**state, "active_agent": None}

    # Build context for chat
    context = {"action": item["action"], "task_id": item["id"], "story_id": item.get("story_id")}

    # Invoke the agent via A2A
    result = await invoke_agent("code_reviewer", item["message"], work_key, context)

    if result.get("success"):
        print(f"[Swarm] Code Reviewer completed: {work_key}")
    else:
        print(f"[Swarm] Code Reviewer failed: {result.get('error')}")

    return {**state, "active_agent": None}


async def qa_node(state: SwarmState) -> SwarmState:
    """QA agent node."""
    work = state.get("last_action")
    if not work:
        return {**state, "active_agent": None}

    item = work["item"]
    work_key = work["work_key"]

    # Claim the item
    claimed = await claim_item("task", item["id"], item["status"])
    if not claimed:
        return {**state, "active_agent": None}

    # Build context for chat
    context = {"action": item["action"], "task_id": item["id"], "story_id": item.get("story_id")}

    # Invoke the agent via A2A
    result = await invoke_agent("qa", item["message"], work_key, context)

    if result.get("success"):
        print(f"[Swarm] QA completed: {work_key}")
    else:
        print(f"[Swarm] QA failed: {result.get('error')}")

    return {**state, "active_agent": None}


async def scrum_master_node(state: SwarmState) -> SwarmState:
    """Scrum Master agent node."""
    work = state.get("last_action")
    if not work:
        return {**state, "active_agent": None}

    item = work["item"]
    work_key = work["work_key"]

    # Build context for chat
    context = {"action": item.get("action", "coordinate")}
    if "story_id" in item:
        context["story_id"] = item["story_id"]
    if "task_id" in item:
        context["task_id"] = item["id"]

    # Invoke the agent via A2A (Scrum Master doesn't claim items, just coordinates)
    result = await invoke_agent("scrum_master", item["message"], work_key, context)

    if result.get("success"):
        print(f"[Swarm] Scrum Master completed: {work_key}")
    else:
        print(f"[Swarm] Scrum Master failed: {result.get('error')}")

    return {**state, "active_agent": None}


async def dynamic_agent_node(state: SwarmState) -> SwarmState:
    """Dynamic agent node - handles user-created agents."""
    work = state.get("last_action")
    if not work:
        return {**state, "active_agent": None}

    agent_id = state.get("active_agent")
    item = work["item"]
    work_key = work["work_key"]

    # Build context for chat
    context = {"action": item.get("action", "work")}
    if "story_id" in item:
        context["story_id"] = item["story_id"]
    if item.get("type") == "task":
        context["task_id"] = item["id"]

    # Invoke the dynamic agent via A2A
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
    """Route to the appropriate agent based on active_agent."""
    active = state.get("active_agent")

    if not active:
        return "end"

    # Map known agents to their nodes
    known_agents = {
        "developer": "developer",
        "tech_lead": "tech_lead",
        "code_reviewer": "code_reviewer",
        "qa": "qa",
        "scrum_master": "scrum_master",
    }

    return known_agents.get(active, "dynamic")


def create_agent_swarm() -> StateGraph:
    """Create the multi-agent swarm graph.

    Returns a compiled StateGraph that orchestrates all agents.
    """
    workflow = StateGraph(SwarmState)

    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("developer", developer_node)
    workflow.add_node("tech_lead", tech_lead_node)
    workflow.add_node("code_reviewer", code_reviewer_node)
    workflow.add_node("qa", qa_node)
    workflow.add_node("scrum_master", scrum_master_node)
    workflow.add_node("dynamic", dynamic_agent_node)

    # Set entry point
    workflow.set_entry_point("router")

    # Add conditional routing from router to agents
    workflow.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "developer": "developer",
            "tech_lead": "tech_lead",
            "code_reviewer": "code_reviewer",
            "qa": "qa",
            "scrum_master": "scrum_master",
            "dynamic": "dynamic",
            "end": END,
        }
    )

    # After each agent, check if we should continue
    for agent in ["developer", "tech_lead", "code_reviewer", "qa", "scrum_master", "dynamic"]:
        workflow.add_conditional_edges(
            agent,
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
                await broadcast_swarm_status("running")
                print("[Swarm] Agent swarm resumed")
            return
        self._running = True
        self._paused = False
        self._task = asyncio.create_task(self._monitor_loop())
        await broadcast_swarm_status("running")
        print("[Swarm] Agent swarm started")

    async def stop(self):
        """Stop the background monitoring loop completely."""
        self._running = False
        self._paused = False
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
            await broadcast_swarm_status("paused")
            print("[Swarm] Agent swarm paused")

    async def resume(self):
        """Resume the swarm after pausing."""
        if self._running and self._paused:
            self._paused = False
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
