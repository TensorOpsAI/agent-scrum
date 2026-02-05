from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.workflow.triggers import trigger_continue_workflow
from app.workflow.orchestrator import orchestrator

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


@router.post("/continue/{story_id}")
async def continue_workflow(
    story_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger workflow continuation for a story.

    This is useful for testing and demo purposes.
    """
    result = await trigger_continue_workflow(story_id, db)
    return result


@router.post("/run-full/{story_id}")
async def run_full_workflow(
    story_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Run the full workflow for a story from current state to completion.

    WARNING: This will process the entire workflow in one request.
    Use for demo purposes only.
    """
    result = await orchestrator.run_full_workflow(story_id, db)
    return result
