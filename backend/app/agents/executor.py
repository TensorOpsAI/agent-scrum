"""
Agent Executor - Executes LangGraph agents with capacity management.

This executor invokes LangGraph ReAct agents and manages their execution
with proper status tracking and capacity limits.
"""
import asyncio
import logging
import random
import time
from typing import Any, Dict, Set
from langchain_core.messages import HumanMessage

from app.agents.langgraph_agents import get_agent
from app.api.websocket.manager import broadcast_agent_activity, broadcast_agent_status

logger = logging.getLogger(__name__)

# --- Swarm-active flag ---------------------------------------------------
# Reads from the per-session contextvar. The flag is toggled by
# ScrumSwarm.start/stop/pause/resume in graph.py.

def is_swarm_active() -> bool:
    """Check whether the swarm is active (session-scoped)."""
    try:
        from app.session import get_current_session
        return get_current_session().swarm_active
    except LookupError:
        return False

# -------------------------------------------------------------------------


def random_delay(min_sec: float, max_sec: float) -> float:
    """Generate a random delay between min and max seconds."""
    return random.uniform(min_sec, max_sec)


# Simulated work delays (in seconds)
WORK_DELAYS = {
    "start": (0.3, 0.5),
    "finishing": (0.3, 0.5),
}

# Minimum time to show "working" status (in seconds)
MIN_WORKING_TIME = 3.0

# Agent capacity - how many items each agent can work on simultaneously
DEFAULT_CAPACITY = 2
AGENT_CAPACITY = {
    "product_owner": 2,
    "developer": 3,
    "tech_lead": 2,
    "code_reviewer": 2,
    "qa": 2,
    "scrum_master": 2,
}


class AgentExecutor:
    """Executor for running LangGraph agents with parallel capacity."""

    def __init__(self):
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._agent_work: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()

    def get_agent_load(self, agent_id: str) -> int:
        """Get the current number of items an agent is working on."""
        return len(self._agent_work.get(agent_id, set()))

    def has_capacity(self, agent_id: str) -> bool:
        """Check if an agent has capacity for more work."""
        current_load = self.get_agent_load(agent_id)
        max_capacity = AGENT_CAPACITY.get(agent_id, DEFAULT_CAPACITY)
        return current_load < max_capacity

    def is_working_on(self, agent_id: str, work_key: str) -> bool:
        """Check if an agent is already working on a specific item."""
        return work_key in self._agent_work.get(agent_id, set())

    async def execute_agent(
        self,
        agent_id: str,
        message: str,
        context: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """Execute a LangGraph agent and return the result.

        Args:
            agent_id: ID of agent to execute (e.g., "product_owner")
            message: Message to send to the agent
            context: Additional context (story_id, task_id, etc.)

        Returns:
            Dict with 'response' from the agent
        """
        context = context or {}
        logger.info(f"[EXECUTOR] execute_agent called. agent_id={agent_id}, message_len={len(message)}, context={context}")

        # Block execution when swarm is paused / stopped
        if not is_swarm_active():
            logger.info(f"[EXECUTOR] Swarm not active — skipping agent {agent_id}")
            return {"response": "Swarm is not active — agent execution skipped.", "skipped": True}

        # Get the LangGraph agent
        agent = get_agent(agent_id)
        if not agent:
            logger.error(f"[EXECUTOR] Agent not found: {agent_id}")
            raise ValueError(f"Agent not found: {agent_id}")

        logger.info(f"[EXECUTOR] Got agent: {type(agent).__name__}")

        # Brief delay before starting
        await asyncio.sleep(random_delay(*WORK_DELAYS["start"]))

        # Track when we started "working"
        working_start_time = time.time()

        # Broadcast status change
        await broadcast_agent_status(agent_id, "working", message[:50])
        await broadcast_agent_activity(
            agent_id,
            "started",
            {"message": message[:100], "context": context}
        )

        try:
            # Execute the LangGraph agent
            logger.info(f"[EXECUTOR] Calling agent.ainvoke for {agent_id}...")
            result = await agent.ainvoke({
                "messages": [HumanMessage(content=message)],
                "context": context,
            })
            logger.info(f"[EXECUTOR] agent.ainvoke returned. Result keys: {result.keys() if isinstance(result, dict) else 'not a dict'}")

            # Extract response from messages
            response_text = ""
            if result.get("messages"):
                last_message = result["messages"][-1]
                response_text = last_message.content if hasattr(last_message, 'content') else str(last_message)
                logger.info(f"[EXECUTOR] Extracted response: {response_text[:200]}...")

            # Ensure minimum working time
            elapsed = time.time() - working_start_time
            if elapsed < MIN_WORKING_TIME:
                await asyncio.sleep(MIN_WORKING_TIME - elapsed)

            # Brief pause before completing
            await asyncio.sleep(random_delay(*WORK_DELAYS["finishing"]))

            await broadcast_agent_activity(
                agent_id,
                "completed",
                {"result": response_text[:100]}
            )

            logger.info(f"[EXECUTOR] Agent {agent_id} completed successfully")
            return {"response": response_text, "raw_result": result}

        except Exception as e:
            logger.error(f"[EXECUTOR] Agent {agent_id} failed: {e}", exc_info=True)
            await broadcast_agent_activity(
                agent_id,
                "failed",
                {"error": str(e)}
            )
            raise

        finally:
            await broadcast_agent_status(agent_id, "idle", None)

    async def execute_agent_background(
        self,
        agent_id: str,
        message: str,
        context: dict[str, Any],
        work_key: str,
    ) -> bool:
        """Execute an agent in the background without blocking.

        Args:
            agent_id: ID of agent to execute
            message: Message to send to the agent
            context: Additional context
            work_key: Unique key identifying this work item

        Returns:
            True if work was started, False if no capacity or already working
        """
        async with self._lock:
            # Initialize agent work set if needed
            if agent_id not in self._agent_work:
                self._agent_work[agent_id] = set()

            # Check if already working on this item
            if self.is_working_on(agent_id, work_key):
                return False

            # Check capacity
            if not self.has_capacity(agent_id):
                return False

            # Mark as working
            self._agent_work[agent_id].add(work_key)

        # Start background task
        task_id = f"{agent_id}:{work_key}"

        async def _run():
            try:
                await self.execute_agent(agent_id, message, context)
            except Exception as e:
                print(f"Background agent execution failed ({agent_id}): {e}")
            finally:
                async with self._lock:
                    self._agent_work[agent_id].discard(work_key)
                    self._running_tasks.pop(task_id, None)

        task = asyncio.create_task(_run())
        self._running_tasks[task_id] = task
        return True

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running async task."""
        task = self._running_tasks.get(task_id)
        if task:
            task.cancel()
            self._running_tasks.pop(task_id, None)
            return True
        return False

    def get_running_tasks(self) -> list[str]:
        """Get list of currently running task IDs."""
        return list(self._running_tasks.keys())

    def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all agents including their current work."""
        return {
            agent_id: {
                "current_load": len(work_items),
                "max_capacity": AGENT_CAPACITY.get(agent_id, DEFAULT_CAPACITY),
                "working_on": list(work_items),
            }
            for agent_id, work_items in self._agent_work.items()
        }
