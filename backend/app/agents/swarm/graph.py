"""
Manager-Worker Swarm - Agent coordination via A2A communication.

Replaces the LangGraph StateGraph with a Manager-Worker topology where:
1. Each board has a Manager agent (e.g., Scrum Master for software_dev)
2. Manager scans for pending work and dispatches to Worker agents via A2A
3. All communication is visible in chat as A2A messages
"""
import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select

from app.db.models import Story, Task, PipelineConfig, DynamicAgent
from app.api.websocket.manager import broadcast_swarm_status
from app.pipeline.templates import TEMPLATE_WORKFLOWS

logger = logging.getLogger(__name__)

# How long before an item is considered "stuck" (in seconds)
STUCK_THRESHOLD = 5

# Minimum working time for visual feedback (seconds)
MIN_WORKING_TIME = 3.0


# ============================================================================
# Action labels for natural Manager→Worker messages
# ============================================================================

ACTION_LABELS = {
    # Software Dev
    "breakdown": "break down",
    "review_tasks": "review the tasks for",
    "implementation": "write the implementation for",
    "code_review": "review the code for",
    "qa_scenarios": "create test scenarios for",
    "qa_run": "run QA tests on",
    # Talent Acquisition
    "screen_resume": "screen the resume for",
    "phone_screen": "conduct a phone screen for",
    "schedule_interview": "schedule an interview for",
    "prepare_offer": "prepare an offer for",
    "evaluate": "evaluate",
    "conduct": "conduct the interview for",
    "review_feedback": "review feedback for",
    "verify": "verify",
    # Sales
    "qualify_lead": "qualify the lead for",
    "create_proposal": "create a proposal for",
    "negotiate": "negotiate the contract for",
    "build_poc": "build a POC for",
    "demo": "run a demo for",
    "review_deal": "review the deal for",
    # CISO
    "assess_threat": "assess the threat for",
    "mitigate": "implement mitigation for",
    "audit": "audit compliance for",
    "implement_control": "implement security controls for",
    "deploy_fix": "deploy the fix for",
    "compliance_review": "review compliance for",
    "verify_mitigation": "verify mitigation for",
}


# ============================================================================
# Core helpers
# ============================================================================

def _get_session_maker():
    """Get the session maker for the current session context."""
    from app.session import get_current_session_maker
    return get_current_session_maker()


async def get_active_agent_ids() -> set[str]:
    """Get the set of currently active agent IDs from the database."""
    async with _get_session_maker()() as db:
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

    async with _get_session_maker()() as db:
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
            for status_key, handler in workflow.get("story_handlers", {}).items():
                agent_role, action = handler[0], handler[1]
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
            for status_key, handler in workflow.get("task_handlers", {}).items():
                agent_role, action = handler[0], handler[1]
                result = await db.execute(
                    select(Task).join(Story, Task.story_id == Story.id).where(
                        Task.status == status_key,
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
                            "status": task.status,
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
    async with _get_session_maker()() as db:
        if item_type == "story":
            result = await db.execute(select(Story).where(Story.id == item_id))
            item = result.scalar_one_or_none()
            if not item or str(item.status) != expected_status:
                return False
        else:
            result = await db.execute(select(Task).where(Task.id == item_id))
            item = result.scalar_one_or_none()
            if not item or item.status != expected_status:
                return False

        if not is_stuck(item.updated_at):
            return False

        item.updated_at = datetime.utcnow()
        await db.commit()
        return True


# ============================================================================
# Manager-Worker dispatch
# ============================================================================

async def get_manager_for_board(board_id: int) -> Optional[str]:
    """Get the manager agent ID for a board (e.g., 'scrum_master_1')."""
    async with _get_session_maker()() as db:
        result = await db.execute(
            select(PipelineConfig.template_id).where(PipelineConfig.id == board_id)
        )
        template_id = result.scalar_one_or_none()
        if not template_id:
            return None

    from app.pipeline.templates import get_template_manager_role
    manager_role = get_template_manager_role(template_id)
    return f"{manager_role}_{board_id}" if manager_role else None


def group_by_board(board_data: dict) -> dict[int, list[dict]]:
    """Group pending stories and tasks by board_id."""
    by_board: dict[int, list[dict]] = {}

    for story in board_data["pending_stories"]:
        bid = story["board_id"]
        work_key = f"{story['action']}:{story['id']}"
        by_board.setdefault(bid, []).append({
            "type": "story",
            "item": story,
            "work_key": work_key,
            "agent": story["agent"],
            "message": story["message"],
        })

    for task in board_data["pending_tasks"]:
        bid = task["board_id"]
        work_key = f"{task['action']}:{task['id']}"
        by_board.setdefault(bid, []).append({
            "type": "task",
            "item": task,
            "work_key": work_key,
            "agent": task["agent"],
            "message": task["message"],
        })

    return by_board


def build_assignment_message(work: dict) -> str:
    """Generate a natural Manager→Worker assignment message."""
    item = work["item"]
    action = item.get("action", "process")
    action_label = ACTION_LABELS.get(action, action.replace("_", " "))
    item_type = "story" if work["type"] == "story" else "task"
    return f"Please {action_label} {item_type} #{item['id']}: {item['title']}"


def build_work_context(work: dict) -> dict:
    """Build context dict for A2A message from a work item."""
    item = work["item"]
    context = {"action": item.get("action", "work")}

    if work["type"] == "story":
        context["story_id"] = item["id"]
        context["board_id"] = item.get("board_id")
    else:
        context["task_id"] = item["id"]
        context["story_id"] = item.get("story_id")
        context["board_id"] = item.get("board_id")

    return context


# ============================================================================
# ScrumSwarm - High-level interface
# ============================================================================

class ScrumSwarm:
    """High-level interface for the Manager-Worker agent swarm."""

    def __init__(self, session_id: str = "default"):
        self._running = False
        self._paused = False
        self._task: Optional[asyncio.Task] = None
        self._session_id = session_id
        self._working_agents: dict[str, str] = {}  # agent_id -> work_key

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

    async def dispatch_one(self, manager_id: str, worker_id: str, work: dict):
        """Manager assigns one work item to a worker via A2A."""
        self._working_agents[worker_id] = work["work_key"]

        try:
            from app.session import get_current_a2a_router

            a2a_router = get_current_a2a_router()
            message = build_assignment_message(work)
            context = build_work_context(work)

            async with _get_session_maker()() as db:
                await a2a_router.send_to_agent(
                    from_agent=manager_id,
                    to_agent=worker_id,
                    message=message,
                    context=context,
                    db=db,
                )

        except Exception as e:
            logger.error(f"[Swarm] {manager_id} → {worker_id} failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._working_agents.pop(worker_id, None)

    async def dispatch_pending_work(self):
        """Manager scans boards and dispatches work to workers via A2A."""
        board_data = await scan_board()
        active_agents = await get_active_agent_ids()

        work_by_board = group_by_board(board_data)

        for board_id, items in work_by_board.items():
            manager_id = await get_manager_for_board(board_id)
            if not manager_id or manager_id not in active_agents:
                continue

            for work in items:
                worker_id = work["agent"]
                if worker_id not in active_agents or worker_id in self._working_agents:
                    continue

                claimed = await claim_item(work["type"], work["item"]["id"], work["item"]["status"])
                if not claimed:
                    continue

                await self.dispatch_one(manager_id, worker_id, work)

    async def run_once(self) -> dict:
        """Run one iteration of the swarm — dispatch all pending work."""
        await self.dispatch_pending_work()
        return {}

    async def start(self):
        """Start the background monitoring loop."""
        from app.session import session_manager, _current_session
        session = session_manager.get_session(self._session_id)
        if session:
            session.swarm_active = True

        if self._running:
            if self._paused:
                self._paused = False
                await broadcast_swarm_status("running")
                logger.info("[Swarm] Agent swarm resumed")
            return
        self._running = True
        self._paused = False
        self._task = asyncio.create_task(self._monitor_loop())
        await broadcast_swarm_status("running")
        logger.info("[Swarm] Agent swarm started")

    async def stop(self):
        """Stop the background monitoring loop completely."""
        self._running = False
        self._paused = False

        from app.session import session_manager
        session = session_manager.get_session(self._session_id)
        if session:
            session.swarm_active = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._working_agents.clear()
        await broadcast_swarm_status("stopped")
        logger.info("[Swarm] Agent swarm stopped")

    async def pause(self):
        """Pause the swarm (agents stop taking new work)."""
        if self._running and not self._paused:
            self._paused = True
            from app.session import session_manager
            session = session_manager.get_session(self._session_id)
            if session:
                session.swarm_active = False
            await broadcast_swarm_status("paused")
            logger.info("[Swarm] Agent swarm paused")

    async def resume(self):
        """Resume the swarm after pausing."""
        if self._running and self._paused:
            self._paused = False
            from app.session import session_manager
            session = session_manager.get_session(self._session_id)
            if session:
                session.swarm_active = True
            await broadcast_swarm_status("running")
            logger.info("[Swarm] Agent swarm resumed")

    async def _monitor_loop(self):
        """Main monitoring loop — restores session contextvar each iteration."""
        await asyncio.sleep(3)

        while self._running:
            try:
                if not self._paused:
                    # Restore session contextvar so all downstream code
                    # sees the correct session-scoped DB, executor, etc.
                    from app.session import session_manager, _current_session
                    session = session_manager.get_session(self._session_id)
                    if session:
                        token = _current_session.set(session)
                        try:
                            await self.run_once()
                        finally:
                            _current_session.reset(token)
                    else:
                        logger.warning(f"[Swarm] Session {self._session_id} not found, stopping")
                        self._running = False
                        break
            except Exception as e:
                logger.error(f"[Swarm] Error: {e}")
                import traceback
                traceback.print_exc()

            interval = random.uniform(3, 6)
            await asyncio.sleep(interval)
