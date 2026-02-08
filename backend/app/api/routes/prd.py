import asyncio
import logging
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.story import PRDSubmission, StoryResponse
from app.workflow.triggers import on_input_submitted

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["input"])


async def _process_input_background(content: str, title: str | None, board_id: int, session):
    """Process input in the background so API returns immediately."""
    logger.info(f"[INPUT] Background processing started. Title: {title}, Board: {board_id}, Content length: {len(content)}")
    try:
        # Restore session contextvar in the background task
        from app.session import _current_session
        token = _current_session.set(session)
        try:
            async with session.session_maker() as db:
                logger.info("[INPUT] Database session created, calling on_input_submitted...")
                result = await on_input_submitted(
                    content=content,
                    title=title,
                    board_id=board_id,
                    db=db,
                )
                logger.info(f"[INPUT] on_input_submitted completed. Result: {result}")
        finally:
            _current_session.reset(token)
    except Exception as e:
        logger.error(f"[INPUT] Error in background processing: {e}", exc_info=True)


@router.post("/input")
async def submit_input(
    submission: PRDSubmission,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Submit input for processing by the agent workflow."""
    from app.session import get_current_session
    session = get_current_session()

    asyncio.create_task(_process_input_background(
        submission.content, submission.title, submission.board_id, session
    ))

    return {
        "message": "Input submitted - processing in background",
        "stories_created": 0,
        "stories": [],
        "response": "Intake agent is analyzing the input. Items will appear shortly.",
    }


# Keep /api/prd as backward-compatible alias
@router.post("/prd")
async def submit_prd(
    submission: PRDSubmission,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Submit a PRD for processing (backward-compatible alias for /api/input)."""
    from app.session import get_current_session
    session = get_current_session()

    asyncio.create_task(_process_input_background(
        submission.content, submission.title, submission.board_id, session
    ))

    return {
        "message": "PRD submitted - processing in background",
        "stories_created": 0,
        "stories": [],
        "response": "Product Owner is analyzing the PRD. Stories will appear shortly.",
    }
