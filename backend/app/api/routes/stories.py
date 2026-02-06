from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional

from app.db.database import get_db
from app.db.models import Story, Task, Comment, TaskStatus, PipelineConfig
from app.schemas.story import (
    StoryCreate, StoryUpdate, StoryResponse, StoryStatusTransition, PRDSubmission
)
from app.schemas.comment import CommentResponse
from app.pipeline.templates import get_valid_statuses

router = APIRouter(prefix="/api/stories", tags=["stories"])


def _story_response(story: Story, task_count: int = 0, completed_count: int = 0) -> StoryResponse:
    return StoryResponse(
        id=story.id,
        board_id=story.board_id,
        title=story.title,
        description=story.description,
        acceptance_criteria=story.acceptance_criteria,
        priority=story.priority,
        status=story.status,
        prd_content=story.prd_content,
        created_at=story.created_at,
        updated_at=story.updated_at,
        task_count=task_count,
        completed_task_count=completed_count,
    )


async def _get_task_counts(db: AsyncSession, story_id: int) -> tuple[int, int]:
    task_count = (await db.execute(
        select(func.count(Task.id)).where(Task.story_id == story_id)
    )).scalar() or 0
    completed_count = (await db.execute(
        select(func.count(Task.id)).where(
            Task.story_id == story_id, Task.status == TaskStatus.DONE
        )
    )).scalar() or 0
    return task_count, completed_count


@router.get("", response_model=list[StoryResponse])
async def list_stories(
    board_id: int = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Story)
    if board_id is not None:
        query = query.where(Story.board_id == board_id)
    if status:
        query = query.where(Story.status == status)
    query = query.order_by(Story.priority.desc(), Story.created_at.desc())

    result = await db.execute(query)
    stories = result.scalars().all()

    response = []
    for story in stories:
        task_count, completed_count = await _get_task_counts(db, story.id)
        response.append(_story_response(story, task_count, completed_count))

    return response


@router.post("", response_model=StoryResponse)
async def create_story(
    story_data: StoryCreate,
    db: AsyncSession = Depends(get_db)
):
    # Validate board exists and get first column
    board_result = await db.execute(
        select(PipelineConfig).where(PipelineConfig.id == story_data.board_id)
    )
    board = board_result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=400, detail=f"Board {story_data.board_id} not found")

    first_status = board.columns[0]["key"]

    story = Story(
        board_id=story_data.board_id,
        title=story_data.title,
        description=story_data.description,
        acceptance_criteria=story_data.acceptance_criteria,
        priority=story_data.priority,
        prd_content=story_data.prd_content,
        status=first_status,
    )
    db.add(story)
    await db.commit()
    await db.refresh(story)

    return _story_response(story)


@router.get("/{story_id}", response_model=StoryResponse)
async def get_story(story_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Story).where(Story.id == story_id))
    story = result.scalar_one_or_none()

    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    task_count, completed_count = await _get_task_counts(db, story.id)
    return _story_response(story, task_count, completed_count)


@router.put("/{story_id}", response_model=StoryResponse)
async def update_story(
    story_id: int,
    story_update: StoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Story).where(Story.id == story_id))
    story = result.scalar_one_or_none()

    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    update_data = story_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(story, field, value)

    await db.commit()
    await db.refresh(story)

    task_count, completed_count = await _get_task_counts(db, story.id)
    return _story_response(story, task_count, completed_count)


@router.post("/{story_id}/status", response_model=StoryResponse)
async def transition_story_status(
    story_id: int,
    transition: StoryStatusTransition,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Story).where(Story.id == story_id).options(selectinload(Story.board))
    )
    story = result.scalar_one_or_none()

    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Validate against the story's board columns
    board_config = {
        "columns": story.board.columns,
    }
    valid = get_valid_statuses(board_config)
    if transition.status not in valid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{transition.status}' for board '{story.board.name}'. Valid: {valid}"
        )

    story.status = transition.status
    await db.commit()
    await db.refresh(story)

    task_count, completed_count = await _get_task_counts(db, story.id)
    return _story_response(story, task_count, completed_count)


@router.delete("/{story_id}")
async def delete_story(story_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Story).where(Story.id == story_id))
    story = result.scalar_one_or_none()

    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    await db.delete(story)
    await db.commit()

    return {"message": "Story deleted successfully"}


@router.get("/{story_id}/comments", response_model=list[CommentResponse])
async def get_story_comments(story_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Story).where(Story.id == story_id))
    story = result.scalar_one_or_none()

    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    comments_query = select(Comment).where(Comment.story_id == story_id).order_by(Comment.created_at)
    result = await db.execute(comments_query)
    comments = result.scalars().all()

    return [
        CommentResponse(
            id=c.id,
            content=c.content,
            agent_type=c.agent_type,
            story_id=c.story_id,
            task_id=c.task_id,
            metadata=c.extra_data,
            created_at=c.created_at,
        )
        for c in comments
    ]
