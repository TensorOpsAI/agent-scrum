"""
Swarm State - Shared state for the multi-agent swarm.
"""
from typing import Annotated, TypedDict, Optional, Any
from langgraph.graph.message import add_messages


class SwarmState(TypedDict):
    """State schema for the agent swarm.

    This state is shared across all agents in the swarm and tracks
    the current board status and work assignments.
    """
    # Messages between agents (for conversational context)
    messages: Annotated[list, add_messages]

    # Current active agent (who should work next)
    active_agent: Optional[str]

    # Board snapshot - what needs attention
    pending_stories: list[dict]  # Stories needing breakdown
    pending_tasks: list[dict]    # Tasks needing work

    # Work tracking
    current_work: dict[str, list[str]]  # agent_id -> list of work_keys

    # Last action taken
    last_action: Optional[dict]

    # Iteration count (to prevent infinite loops)
    iteration: int
