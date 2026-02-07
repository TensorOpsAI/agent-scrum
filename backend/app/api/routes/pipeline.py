"""
Pipeline/Board API Routes - Manage pipeline templates and boards.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.database import get_db
from app.db.models import PipelineConfig, Story
from app.db.seed import seed_agents_for_board
from app.schemas.pipeline import (
    PipelineTemplateResponse,
    PipelineColumn,
    BoardCreateRequest,
    BoardResponse,
)
from app.pipeline.templates import (
    PIPELINE_TEMPLATES,
    get_template_by_id,
)
from app.api.websocket.manager import manager

router = APIRouter(prefix="/api", tags=["pipeline"])


# ============================================================================
# Templates
# ============================================================================

@router.get("/pipeline/templates", response_model=list[PipelineTemplateResponse])
async def list_templates():
    """List all preset pipeline templates."""
    return [
        PipelineTemplateResponse(
            template_id=t["template_id"],
            name=t["name"],
            columns=[PipelineColumn(**c) for c in t["columns"]],
            agent_automation=t["agent_automation"],
            item_noun=t["item_noun"],
            has_tasks=t["has_tasks"],
            sub_item_noun=t.get("sub_item_noun", "Task"),
            input_noun=t.get("input_noun", "PRD"),
            epic_noun=t.get("epic_noun", "Epic"),
            input_placeholder=t.get("input_placeholder"),
            sub_item_statuses=t.get("sub_item_statuses"),
            item_source=t.get("item_source", "internal"),
        )
        for t in PIPELINE_TEMPLATES
    ]


# ============================================================================
# Boards
# ============================================================================

def _board_response(board: PipelineConfig, story_count: int = 0) -> BoardResponse:
    return BoardResponse(
        id=board.id,
        template_id=board.template_id,
        name=board.name,
        columns=[PipelineColumn(**c) for c in board.columns],
        agent_automation=board.agent_automation,
        item_noun=board.item_noun,
        has_tasks=board.has_tasks,
        sub_item_noun=board.sub_item_noun or "Task",
        input_noun=board.input_noun or "PRD",
        epic_noun=board.epic_noun or "Epic",
        input_placeholder=board.input_placeholder,
        sub_item_statuses=board.sub_item_statuses,
        item_source=board.item_source or "internal",
        story_count=story_count,
    )


@router.get("/boards", response_model=list[BoardResponse])
async def list_boards(db: AsyncSession = Depends(get_db)):
    """List all boards."""
    result = await db.execute(
        select(PipelineConfig).order_by(PipelineConfig.id)
    )
    boards = result.scalars().all()

    responses = []
    for board in boards:
        count_result = await db.execute(
            select(func.count(Story.id)).where(Story.board_id == board.id)
        )
        story_count = count_result.scalar() or 0
        responses.append(_board_response(board, story_count))

    return responses


@router.post("/boards", response_model=BoardResponse)
async def create_board(
    request: BoardCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new board from a template."""
    template = get_template_by_id(request.template_id)
    if not template:
        raise HTTPException(status_code=400, detail=f"Unknown template: {request.template_id}")

    name = request.name or template["name"]

    board = PipelineConfig(
        template_id=template["template_id"],
        name=name,
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

    # Seed domain-specific agents for this board
    agents_created = await seed_agents_for_board(db, board)
    if agents_created > 0:
        await db.commit()

    resp = _board_response(board)

    await manager.broadcast("board:created", resp.model_dump())

    return resp


@router.get("/boards/{board_id}", response_model=BoardResponse)
async def get_board(board_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single board by ID."""
    result = await db.execute(
        select(PipelineConfig).where(PipelineConfig.id == board_id)
    )
    board = result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    count_result = await db.execute(
        select(func.count(Story.id)).where(Story.board_id == board.id)
    )
    story_count = count_result.scalar() or 0

    return _board_response(board, story_count)


@router.delete("/boards/{board_id}")
async def delete_board(board_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a board and cascade delete its stories."""
    result = await db.execute(
        select(PipelineConfig).where(PipelineConfig.id == board_id)
    )
    board = result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    await db.delete(board)
    await db.commit()

    await manager.broadcast("board:deleted", {"id": board_id})

    return {"message": "Board deleted successfully"}
