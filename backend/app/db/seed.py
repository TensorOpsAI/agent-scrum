"""
Database Seed Data - Default agents that are created on first run.

These agents can be deleted/modified by the user through the UI,
just like any other agent.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DynamicAgent


# Default agents that ship with the system
DEFAULT_AGENTS = [
    {
        "id": "product_owner",
        "name": "Product Owner",
        "description": "Parses PRDs and creates user stories with acceptance criteria",
        "template": None,
        "tools": ["prd_parser", "story_generator"],
        "skills": [
            {
                "id": "parse_prd",
                "name": "Parse PRD",
                "description": "Parse a Product Requirements Document and extract user stories",
                "tags": ["prd", "stories", "requirements"],
                "examples": ["Parse this PRD and create stories"],
            },
            {
                "id": "create_story",
                "name": "Create Story",
                "description": "Create a new user story with acceptance criteria",
                "tags": ["story", "acceptance-criteria"],
                "examples": ["Create a story for user authentication"],
            },
        ],
        "capabilities": {
            "streaming": False,
            "push_notifications": False,
            "state_transition_history": True,
        },
        "is_active": True,
    },
    {
        "id": "tech_lead",
        "name": "Tech Lead",
        "description": "Reviews task breakdowns and provides technical guidance",
        "template": None,
        "tools": ["task_reviewer", "architecture_analyzer"],
        "skills": [
            {
                "id": "review_tasks",
                "name": "Review Tasks",
                "description": "Review task breakdown for a story and approve or request changes",
                "tags": ["review", "tasks", "approval"],
                "examples": ["Review the tasks for story #1"],
            },
            {
                "id": "technical_guidance",
                "name": "Technical Guidance",
                "description": "Provide technical guidance on implementation approach",
                "tags": ["guidance", "architecture"],
                "examples": ["How should we implement this feature?"],
            },
        ],
        "capabilities": {
            "streaming": False,
            "push_notifications": False,
            "state_transition_history": True,
        },
        "is_active": True,
    },
    {
        "id": "developer",
        "name": "Developer",
        "description": "Breaks down stories into tasks and creates implementation notes",
        "template": None,
        "tools": ["story_breakdown", "code_generator"],
        "skills": [
            {
                "id": "breakdown_story",
                "name": "Breakdown Story",
                "description": "Break down a user story into implementable tasks",
                "tags": ["breakdown", "tasks", "planning"],
                "examples": ["Break down story #1 into tasks"],
            },
            {
                "id": "implementation_notes",
                "name": "Implementation Notes",
                "description": "Create detailed implementation notes for a task",
                "tags": ["implementation", "notes", "code"],
                "examples": ["Write implementation notes for task #1"],
            },
        ],
        "capabilities": {
            "streaming": False,
            "push_notifications": False,
            "state_transition_history": True,
        },
        "is_active": True,
    },
    {
        "id": "code_reviewer",
        "name": "Code Reviewer",
        "description": "Reviews implementation notes and provides feedback",
        "template": None,
        "tools": ["code_analyzer", "security_scanner"],
        "skills": [
            {
                "id": "review_implementation",
                "name": "Review Implementation",
                "description": "Review implementation notes and approve or request changes",
                "tags": ["review", "code", "feedback"],
                "examples": ["Review implementation for task #1"],
            },
        ],
        "capabilities": {
            "streaming": False,
            "push_notifications": False,
            "state_transition_history": True,
        },
        "is_active": True,
    },
    {
        "id": "qa",
        "name": "QA",
        "description": "Creates test scenarios and runs simulated tests",
        "template": None,
        "tools": ["test_generator", "test_runner"],
        "skills": [
            {
                "id": "create_test_scenarios",
                "name": "Create Test Scenarios",
                "description": "Create test scenarios for a task or story",
                "tags": ["test", "scenarios", "qa"],
                "examples": ["Create test scenarios for task #1"],
            },
            {
                "id": "run_tests",
                "name": "Run Tests",
                "description": "Execute simulated tests and report results",
                "tags": ["test", "execution", "results"],
                "examples": ["Run tests for story #1"],
            },
        ],
        "capabilities": {
            "streaming": False,
            "push_notifications": False,
            "state_transition_history": True,
        },
        "is_active": True,
    },
    # Note: Scrum Master is available but not active by default
    # The swarm itself acts as the coordinator
    {
        "id": "scrum_master",
        "name": "Scrum Master",
        "description": "Coordinates the team workflow and unblocks stuck tasks (optional)",
        "template": None,
        "tools": ["workflow_monitor", "blocker_resolver"],
        "skills": [
            {
                "id": "check_blockers",
                "name": "Check Blockers",
                "description": "Identify stuck or blocked work items",
                "tags": ["blockers", "workflow", "monitoring"],
                "examples": ["Check for blocked tasks"],
            },
            {
                "id": "facilitate",
                "name": "Facilitate",
                "description": "Coordinate team communication and workflow",
                "tags": ["coordination", "communication", "workflow"],
                "examples": ["Help unblock task #1"],
            },
        ],
        "capabilities": {
            "streaming": False,
            "push_notifications": False,
            "state_transition_history": True,
        },
        "is_active": False,  # Not active by default - swarm handles coordination
    },
]


async def seed_default_agents(db: AsyncSession) -> int:
    """Seed the database with default agents if they don't exist.

    Returns the number of agents created.
    """
    created_count = 0

    for agent_data in DEFAULT_AGENTS:
        # Check if agent already exists
        result = await db.execute(
            select(DynamicAgent).where(DynamicAgent.id == agent_data["id"])
        )
        existing = result.scalar_one_or_none()

        if not existing:
            agent = DynamicAgent(
                id=agent_data["id"],
                name=agent_data["name"],
                description=agent_data["description"],
                template=agent_data["template"],
                tools=agent_data["tools"],
                skills=agent_data["skills"],
                capabilities=agent_data["capabilities"],
                is_active=agent_data["is_active"],
            )
            db.add(agent)
            created_count += 1
            print(f"[Seed] Created default agent: {agent_data['id']}")

    if created_count > 0:
        await db.commit()

    return created_count
