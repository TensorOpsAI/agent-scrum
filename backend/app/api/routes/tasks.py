from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db.database import get_db
from app.db.models import Task, Story, Comment, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskStatusTransition
from app.schemas.comment import CommentResponse

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    story_id: Optional[int] = None,
    status: Optional[TaskStatus] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Task)

    if story_id:
        query = query.where(Task.story_id == story_id)
    if status:
        query = query.where(Task.status == status)

    query = query.order_by(Task.created_at.desc())

    result = await db.execute(query)
    tasks = result.scalars().all()

    return [TaskResponse.model_validate(t) for t in tasks]


@router.post("", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    # Verify story exists
    result = await db.execute(select(Story).where(Story.id == task_data.story_id))
    story = result.scalar_one_or_none()

    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    task = Task(**task_data.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)

    return TaskResponse.model_validate(task)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskResponse.model_validate(task)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)

    return TaskResponse.model_validate(task)


@router.post("/{task_id}/status", response_model=TaskResponse)
async def transition_task_status(
    task_id: int,
    transition: TaskStatusTransition,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = transition.status
    await db.commit()
    await db.refresh(task)

    return TaskResponse.model_validate(task)


@router.delete("/{task_id}")
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await db.delete(task)
    await db.commit()

    return {"message": "Task deleted successfully"}


@router.get("/{task_id}/comments", response_model=list[CommentResponse])
async def get_task_comments(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    comments_query = select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at)
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
