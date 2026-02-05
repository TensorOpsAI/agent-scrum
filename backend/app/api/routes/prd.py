import asyncio
import logging
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db, async_session_maker
from app.schemas.story import PRDSubmission, StoryResponse
from app.workflow.triggers import on_prd_submitted

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["prd"])


async def _process_prd_background(prd_content: str, title: str | None):
    """Process PRD in the background so API returns immediately."""
    logger.info(f"[PRD] Background processing started. Title: {title}, Content length: {len(prd_content)}")
    try:
        async with async_session_maker() as db:
            logger.info("[PRD] Database session created, calling on_prd_submitted...")
            result = await on_prd_submitted(
                prd_content=prd_content,
                title=title,
                db=db,
            )
            logger.info(f"[PRD] on_prd_submitted completed. Result: {result}")
    except Exception as e:
        logger.error(f"[PRD] Error in background processing: {e}", exc_info=True)


@router.post("/prd")
async def submit_prd(
    submission: PRDSubmission,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Submit a PRD for processing by the agent workflow.

    The Product Owner agent will parse the PRD and create stories.
    Returns immediately while processing happens in the background.
    Stories will appear on the board as they are created via WebSocket.
    """
    # Start background processing
    asyncio.create_task(_process_prd_background(submission.content, submission.title))

    return {
        "message": "PRD submitted - processing in background",
        "stories_created": 0,
        "stories": [],
        "response": "Product Owner is analyzing the PRD. Stories will appear shortly.",
    }
