"""
Database Seed Data - Default agents that are created on first run.

Agents are now seeded per-board using the template's agent definitions.
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DynamicAgent, PipelineConfig
from app.pipeline.templates import get_template_by_id, PIPELINE_TEMPLATES


def get_template_agents(template_id: str) -> list[dict]:
    """Get agent definitions from a template."""
    template = get_template_by_id(template_id)
    if not template:
        return []
    return template.get("agents", [])


# Keep DEFAULT_AGENTS for backward-compat imports (used by conftest assertions)
DEFAULT_AGENTS = get_template_agents("software_dev")


async def seed_agents_for_board(db: AsyncSession, board: PipelineConfig) -> int:
    """Seed agents for a specific board based on its template.

    Returns the number of agents created.
    """
    agents_def = get_template_agents(board.template_id)
    created_count = 0

    for agent_def in agents_def:
        agent_id = f"{agent_def['role']}_{board.id}"

        # Check if agent already exists
        result = await db.execute(
            select(DynamicAgent).where(DynamicAgent.id == agent_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            continue

        is_active = agent_def.get("is_active", True)

        # Convert tool strings into A2A skill objects
        tool_names = agent_def.get("tools", [])
        skills = [
            {
                "id": tool_name,
                "name": tool_name.replace("_", " ").title(),
                "description": f"{tool_name.replace('_', ' ').title()} capability",
            }
            for tool_name in tool_names
        ]

        agent = DynamicAgent(
            id=agent_id,
            name=agent_def["name"],
            description=agent_def["description"],
            role=agent_def["role"],
            template=board.template_id,
            board_id=board.id,
            tools=tool_names,
            skills=skills,
            capabilities={
                "streaming": False,
                "push_notifications": False,
                "state_transition_history": True,
            },
            is_active=is_active,
        )
        db.add(agent)
        created_count += 1
        print(f"[Seed] Created agent: {agent_id} for board '{board.name}'")

    return created_count


async def seed_default_agents(db: AsyncSession) -> int:
    """Seed the database with default board and its agents if they don't exist.

    Returns the number of agents created.
    """
    # Seed default board if no boards exist
    board_count_result = await db.execute(
        select(func.count(PipelineConfig.id))
    )
    board_count = board_count_result.scalar() or 0

    board = None
    if board_count == 0:
        template = get_template_by_id("software_dev")
        board = PipelineConfig(
            template_id=template["template_id"],
            name=template["name"],
            columns=template["columns"],
            agent_automation=template["agent_automation"],
            item_noun=template["item_noun"],
            has_tasks=template["has_tasks"],
            sub_item_noun=template.get("sub_item_noun", "Task"),
            input_noun=template.get("input_noun", "PRD"),
            epic_noun=template.get("epic_noun", "Epic"),
            input_placeholder=template.get("input_placeholder"),
            sub_item_statuses=template.get("sub_item_statuses"),
            item_source=template.get("item_source", "internal"),
        )
        db.add(board)
        await db.commit()
        await db.refresh(board)
        print("[Seed] Created default Software Development board")
    else:
        # Get the first board
        result = await db.execute(
            select(PipelineConfig).order_by(PipelineConfig.id).limit(1)
        )
        board = result.scalar_one_or_none()

    # Seed agents for the default board
    created_count = 0
    if board:
        # Check if board already has agents
        agent_count_result = await db.execute(
            select(func.count(DynamicAgent.id)).where(DynamicAgent.board_id == board.id)
        )
        agent_count = agent_count_result.scalar() or 0

        if agent_count == 0:
            created_count = await seed_agents_for_board(db, board)
            if created_count > 0:
                await db.commit()

    return created_count
