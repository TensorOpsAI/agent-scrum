"""
Agents API - Unified endpoint for all agents (from database).

All agents are stored in the database and can be added/removed dynamically.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.models import DynamicAgent
def _get_working_agents() -> dict:
    """Get working agents dict from session-scoped swarm."""
    try:
        from app.session import get_current_swarm
        swarm = get_current_swarm()
        return swarm._working_agents
    except LookupError:
        return {}

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("")
async def list_agents(
    board_id: Optional[int] = Query(None, description="Filter agents by board ID"),
    db: AsyncSession = Depends(get_db),
):
    """List all agents from the database with their current status."""
    # Get all active agents from database
    query = select(DynamicAgent).where(DynamicAgent.is_active == True)
    if board_id is not None:
        query = query.where(DynamicAgent.board_id == board_id)
    query = query.order_by(DynamicAgent.created_at)
    result = await db.execute(query)
    db_agents = result.scalars().all()

    agents = []
    for agent in db_agents:
        # Determine status based on working agents
        working = _get_working_agents()
        is_working = agent.id in working
        status = "working" if is_working else "idle"
        current_task = working.get(agent.id) if is_working else None

        agents.append({
            "id": agent.id,
            "type": agent.role or agent.id,
            "name": agent.name,
            "description": agent.description or "",
            "status": status,
            "current_task": current_task,
            "is_active": agent.is_active,
            "skills": agent.skills or [],
        })

    return agents


@router.get("/{agent_id}")
async def get_agent_info(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Get detailed information about a specific agent."""
    result = await db.execute(
        select(DynamicAgent).where(DynamicAgent.id == agent_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    working = _get_working_agents()
    is_working = agent.id in working
    status = "working" if is_working else "idle"
    current_task = working.get(agent.id) if is_working else None

    return {
        "id": agent.id,
        "type": agent.role or agent.id,
        "name": agent.name,
        "description": agent.description or "",
        "skills": agent.skills or [],
        "status": status,
        "current_task": current_task,
        "is_active": agent.is_active,
    }


@router.get("/{agent_id}/status")
async def get_agent_status(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Get the current status of an agent."""
    result = await db.execute(
        select(DynamicAgent).where(DynamicAgent.id == agent_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    working = _get_working_agents()
    is_working = agent.id in working
    status = "working" if is_working else "idle"
    current_task = working.get(agent.id) if is_working else None

    return {
        "id": agent.id,
        "type": agent.role or agent.id,
        "name": agent.name,
        "status": status,
        "current_task": current_task,
    }
