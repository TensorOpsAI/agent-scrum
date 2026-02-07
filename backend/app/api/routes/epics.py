"""
Epic API Routes - CRUD for epics (grouping entity above stories).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.db.database import get_db
from app.db.models import Epic, Story, PipelineConfig
from app.schemas.epic import EpicCreate, EpicUpdate, EpicResponse
from app.schemas.story import StoryResponse
from app.api.routes.stories import _story_response, _get_task_counts

router = APIRouter(prefix="/api/epics", tags=["epics"])


def _epic_response(epic: Epic, story_count: int = 0) -> EpicResponse:
    return EpicResponse(
        id=epic.id,
        board_id=epic.board_id,
        title=epic.title,
        description=epic.description,
        status=epic.status,
        created_at=epic.created_at,
        updated_at=epic.updated_at,
        story_count=story_count,
    )


@router.get("", response_model=list[EpicResponse])
async def list_epics(
    board_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all epics, optionally filtered by board."""
    query = select(Epic)
    if board_id is not None:
        query = query.where(Epic.board_id == board_id)
    query = query.order_by(Epic.created_at.desc())

    result = await db.execute(query)
    epics = result.scalars().all()

    responses = []
    for epic in epics:
        count_result = await db.execute(
            select(func.count(Story.id)).where(Story.epic_id == epic.id)
        )
        story_count = count_result.scalar() or 0
        responses.append(_epic_response(epic, story_count))

    return responses


@router.post("", response_model=EpicResponse)
async def create_epic(
    epic_data: EpicCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new epic."""
    # Validate board exists
    board_result = await db.execute(
        select(PipelineConfig).where(PipelineConfig.id == epic_data.board_id)
    )
    board = board_result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=400, detail=f"Board {epic_data.board_id} not found")

    epic = Epic(
        board_id=epic_data.board_id,
        title=epic_data.title,
        description=epic_data.description,
    )
    db.add(epic)
    await db.commit()
    await db.refresh(epic)

    return _epic_response(epic)


@router.get("/{epic_id}", response_model=EpicResponse)
async def get_epic(epic_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single epic by ID."""
    result = await db.execute(select(Epic).where(Epic.id == epic_id))
    epic = result.scalar_one_or_none()

    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")

    count_result = await db.execute(
        select(func.count(Story.id)).where(Story.epic_id == epic.id)
    )
    story_count = count_result.scalar() or 0

    return _epic_response(epic, story_count)


@router.put("/{epic_id}", response_model=EpicResponse)
async def update_epic(
    epic_id: int,
    epic_update: EpicUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an epic."""
    result = await db.execute(select(Epic).where(Epic.id == epic_id))
    epic = result.scalar_one_or_none()

    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")

    update_data = epic_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(epic, field, value)

    await db.commit()
    await db.refresh(epic)

    count_result = await db.execute(
        select(func.count(Story.id)).where(Story.epic_id == epic.id)
    )
    story_count = count_result.scalar() or 0

    return _epic_response(epic, story_count)


@router.delete("/{epic_id}")
async def delete_epic(epic_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an epic. Stories are NOT deleted, just unlinked."""
    result = await db.execute(select(Epic).where(Epic.id == epic_id))
    epic = result.scalar_one_or_none()

    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")

    # Unlink stories from this epic
    stories_result = await db.execute(
        select(Story).where(Story.epic_id == epic_id)
    )
    for story in stories_result.scalars().all():
        story.epic_id = None

    await db.delete(epic)
    await db.commit()

    return {"message": "Epic deleted successfully"}


@router.get("/{epic_id}/stories", response_model=list[StoryResponse])
async def get_epic_stories(epic_id: int, db: AsyncSession = Depends(get_db)):
    """Get all stories belonging to an epic."""
    result = await db.execute(select(Epic).where(Epic.id == epic_id))
    epic = result.scalar_one_or_none()

    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")

    stories_result = await db.execute(
        select(Story).where(Story.epic_id == epic_id).order_by(Story.priority.desc(), Story.created_at.desc())
    )
    stories = stories_result.scalars().all()

    responses = []
    for story in stories:
        task_count, completed_count = await _get_task_counts(db, story.id)
        responses.append(_story_response(story, task_count, completed_count))

    return responses
