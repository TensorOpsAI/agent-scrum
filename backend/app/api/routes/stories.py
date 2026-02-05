from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.db.database import get_db
from app.db.models import Story, Task, Comment, StoryStatus, TaskStatus
from app.schemas.story import (
    StoryCreate, StoryUpdate, StoryResponse, StoryStatusTransition, PRDSubmission
)
from app.schemas.comment import CommentResponse

router = APIRouter(prefix="/api/stories", tags=["stories"])


@router.get("", response_model=list[StoryResponse])
async def list_stories(
    status: Optional[StoryStatus] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Story)
    if status:
        query = query.where(Story.status == status)
    query = query.order_by(Story.priority.desc(), Story.created_at.desc())

    result = await db.execute(query)
    stories = result.scalars().all()

    response = []
    for story in stories:
        task_count_query = select(func.count(Task.id)).where(Task.story_id == story.id)
        completed_count_query = select(func.count(Task.id)).where(
            Task.story_id == story.id,
            Task.status == TaskStatus.DONE
        )

        task_count = (await db.execute(task_count_query)).scalar() or 0
        completed_count = (await db.execute(completed_count_query)).scalar() or 0

        story_dict = {
            "id": story.id,
            "title": story.title,
            "description": story.description,
            "acceptance_criteria": story.acceptance_criteria,
            "priority": story.priority,
            "status": story.status,
            "prd_content": story.prd_content,
            "created_at": story.created_at,
            "updated_at": story.updated_at,
            "task_count": task_count,
            "completed_task_count": completed_count
        }
        response.append(StoryResponse(**story_dict))

    return response


@router.post("", response_model=StoryResponse)
async def create_story(
    story_data: StoryCreate,
    db: AsyncSession = Depends(get_db)
):
    story = Story(**story_data.model_dump())
    db.add(story)
    await db.commit()
    await db.refresh(story)

    return StoryResponse(
        id=story.id,
        title=story.title,
        description=story.description,
        acceptance_criteria=story.acceptance_criteria,
        priority=story.priority,
        status=story.status,
        prd_content=story.prd_content,
        created_at=story.created_at,
        updated_at=story.updated_at,
        task_count=0,
        completed_task_count=0
    )


@router.get("/{story_id}", response_model=StoryResponse)
async def get_story(story_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Story).where(Story.id == story_id))
    story = result.scalar_one_or_none()

    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    task_count_query = select(func.count(Task.id)).where(Task.story_id == story.id)
    completed_count_query = select(func.count(Task.id)).where(
        Task.story_id == story.id,
        Task.status == TaskStatus.DONE
    )

    task_count = (await db.execute(task_count_query)).scalar() or 0
    completed_count = (await db.execute(completed_count_query)).scalar() or 0

    return StoryResponse(
        id=story.id,
        title=story.title,
        description=story.description,
        acceptance_criteria=story.acceptance_criteria,
        priority=story.priority,
        status=story.status,
        prd_content=story.prd_content,
        created_at=story.created_at,
        updated_at=story.updated_at,
        task_count=task_count,
        completed_task_count=completed_count
    )


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

    task_count_query = select(func.count(Task.id)).where(Task.story_id == story.id)
    completed_count_query = select(func.count(Task.id)).where(
        Task.story_id == story.id,
        Task.status == TaskStatus.DONE
    )

    task_count = (await db.execute(task_count_query)).scalar() or 0
    completed_count = (await db.execute(completed_count_query)).scalar() or 0

    return StoryResponse(
        id=story.id,
        title=story.title,
        description=story.description,
        acceptance_criteria=story.acceptance_criteria,
        priority=story.priority,
        status=story.status,
        prd_content=story.prd_content,
        created_at=story.created_at,
        updated_at=story.updated_at,
        task_count=task_count,
        completed_task_count=completed_count
    )


@router.post("/{story_id}/status", response_model=StoryResponse)
async def transition_story_status(
    story_id: int,
    transition: StoryStatusTransition,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Story).where(Story.id == story_id))
    story = result.scalar_one_or_none()

    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    story.status = transition.status
    await db.commit()
    await db.refresh(story)

    task_count_query = select(func.count(Task.id)).where(Task.story_id == story.id)
    completed_count_query = select(func.count(Task.id)).where(
        Task.story_id == story.id,
        Task.status == TaskStatus.DONE
    )

    task_count = (await db.execute(task_count_query)).scalar() or 0
    completed_count = (await db.execute(completed_count_query)).scalar() or 0

    return StoryResponse(
        id=story.id,
        title=story.title,
        description=story.description,
        acceptance_criteria=story.acceptance_criteria,
        priority=story.priority,
        status=story.status,
        prd_content=story.prd_content,
        created_at=story.created_at,
        updated_at=story.updated_at,
        task_count=task_count,
        completed_task_count=completed_count
    )


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
