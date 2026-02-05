"""
A2A Agent Registry - Discovery and registration for LangGraph agents.

This registry enables A2A protocol discovery for agents and tracks their status.
"""
from typing import Any
from app.schemas.a2a import AgentCard, AgentSkill, AgentCapabilities
from app.agents.langgraph_agents import get_agent, get_agent_skills, AGENT_FACTORIES


class AgentRegistry:
    """Registry for A2A agent discovery.

    Provides agent cards and status tracking for the A2A protocol.
    Works with LangGraph agents defined in langgraph_agents.py.
    """

    def __init__(self):
        # Track agent status
        self._status: dict[str, str] = {}  # agent_id -> "idle" | "working"
        self._current_task: dict[str, str | None] = {}  # agent_id -> current task description

    def get_agent_card(self, agent_id: str, base_url: str = "") -> AgentCard | None:
        """Get an agent's A2A discovery card."""
        if agent_id not in AGENT_FACTORIES:
            return None

        skills = get_agent_skills(agent_id)
        skill_objects = [
            AgentSkill(
                id=s["id"],
                name=s["name"],
                description=s["description"],
                tags=s.get("tags", []),
                examples=s.get("examples", []),
            )
            for s in skills
        ]

        # Agent metadata
        metadata = AGENT_METADATA.get(agent_id, {})

        return AgentCard(
            name=metadata.get("name", agent_id.replace("_", " ").title()),
            description=metadata.get("description", ""),
            url=f"{base_url}/api/agents/{agent_id}",
            skills=skill_objects,
            capabilities=AgentCapabilities(
                streaming=False,
                push_notifications=False,
                state_transition_history=True,
            ),
        )

    def list_agents(self, base_url: str = "") -> list[dict]:
        """List all available agents with their A2A cards."""
        result = []
        for agent_id in AGENT_FACTORIES.keys():
            card = self.get_agent_card(agent_id, base_url)
            if card:
                result.append({
                    "id": agent_id,
                    "type": agent_id,
                    "name": card.name,
                    "description": card.description,
                    "status": self._status.get(agent_id, "idle"),
                    "current_task": self._current_task.get(agent_id),
                    "skills": [s.model_dump() for s in card.skills],
                })
        return result

    def set_status(self, agent_id: str, status: str, current_task: str | None = None):
        """Update an agent's status."""
        self._status[agent_id] = status
        self._current_task[agent_id] = current_task

    def get_status(self, agent_id: str) -> dict:
        """Get an agent's current status."""
        return {
            "status": self._status.get(agent_id, "idle"),
            "current_task": self._current_task.get(agent_id),
        }

    def is_available(self, agent_id: str) -> bool:
        """Check if an agent is available (exists and idle)."""
        return agent_id in AGENT_FACTORIES and self._status.get(agent_id, "idle") == "idle"


# Agent display metadata
AGENT_METADATA = {
    "product_owner": {
        "name": "Product Owner",
        "description": "Parses PRDs and creates user stories with acceptance criteria",
    },
    "tech_lead": {
        "name": "Tech Lead",
        "description": "Reviews task breakdowns and provides technical guidance",
    },
    "developer": {
        "name": "Developer",
        "description": "Breaks down stories into tasks and creates implementation notes",
    },
    "code_reviewer": {
        "name": "Code Reviewer",
        "description": "Reviews implementation notes and provides feedback",
    },
    "qa": {
        "name": "QA",
        "description": "Creates test scenarios and runs simulated tests",
    },
    "scrum_master": {
        "name": "Scrum Master",
        "description": "Coordinates the team workflow and unblocks stuck tasks",
    },
}

# Global registry instance
registry = AgentRegistry()
