"""
Simulation API - Generate realistic fake items for non-dev boards.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.models import PipelineConfig, Epic
from app.agents.simulation.generators import generate_items
from app.agents.tools.db_tools import create_story

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/boards", tags=["simulate"])


class SimulateRequest(BaseModel):
    epic_id: Optional[int] = None
    count: int = 5


@router.post("/{board_id}/simulate")
async def simulate_items(
    board_id: int,
    request: SimulateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate simulated items for a board.

    Uses template-specific generators to create realistic fake data
    (candidates, leads, incidents) and places them on the board.
    """
    # Get board
    result = await db.execute(
        select(PipelineConfig).where(PipelineConfig.id == board_id)
    )
    board = result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail=f"Board {board_id} not found")

    # Get epic context if provided
    context = None
    if request.epic_id:
        epic_result = await db.execute(
            select(Epic).where(Epic.id == request.epic_id)
        )
        epic = epic_result.scalar_one_or_none()
        if epic:
            context = f"{epic.title}: {epic.description or ''}"

    # Generate items
    items = generate_items(
        template_id=board.template_id,
        count=request.count,
        context=context,
    )

    if not items:
        raise HTTPException(
            status_code=400,
            detail=f"No generator available for template '{board.template_id}'. Simulation is for external-source boards (TA, Sales, CISO).",
        )

    # Create stories for each generated item
    created = []
    for item in items:
        try:
            story_result = await create_story.ainvoke({
                "title": item["title"],
                "description": item["description"],
                "acceptance_criteria": item.get("acceptance_criteria", ""),
                "board_id": board_id,
                "priority": 1,
                "epic_id": request.epic_id,
            })
            created.append(story_result)
        except Exception as e:
            logger.error(f"Error creating simulated item: {e}")

    return {
        "success": True,
        "count": len(created),
        "items": created,
    }
