"""Settings API - Configuration and control endpoints."""
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.config import get_settings
from app.db.database import get_db
from app.db.seed import seed_default_agents

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsResponse(BaseModel):
    has_api_key: bool
    simulate_mode: bool
    model: str
    swarm_status: str


@router.get("", response_model=SettingsResponse)
async def get_current_settings(request: Request):
    """Get current settings (without exposing the actual API key)."""
    from app.session import get_current_session, get_current_api_key, get_current_swarm

    settings = get_settings()
    session = get_current_session()
    api_key = get_current_api_key()
    swarm = get_current_swarm()

    return SettingsResponse(
        has_api_key=bool(api_key),
        simulate_mode=session.simulate_mode,
        model=settings.gemini_model,
        swarm_status=swarm.status,
    )


@router.post("/simulate-mode")
async def toggle_simulate_mode(enabled: bool = True):
    """Toggle simulation mode on/off."""
    from app.session import get_current_session
    session = get_current_session()
    session.simulate_mode = enabled
    return {
        "success": True,
        "simulate_mode": enabled,
    }


@router.post("/reset")
async def reset_all_data(db: AsyncSession = Depends(get_db)):
    """Reset the board and swarm. Preserves settings."""
    try:
        from app.session import get_current_swarm

        swarm = get_current_swarm()
        await swarm.stop()

        # Delete everything including boards (cascade deletes stories)
        await db.execute(text("DELETE FROM comments"))
        await db.execute(text("DELETE FROM tasks"))
        await db.execute(text("DELETE FROM stories"))
        await db.execute(text("DELETE FROM agent_messages"))
        await db.execute(text("DELETE FROM dynamic_agents"))
        await db.execute(text("DELETE FROM custom_tools"))
        await db.execute(text("DELETE FROM pipeline_configs"))
        await db.commit()

        # Re-seed default agents and default board
        await seed_default_agents(db)

        # Restart the swarm
        await swarm.start()

        return {
            "success": True,
            "message": "All data has been reset.",
        }
    except Exception as e:
        await db.rollback()
        return {
            "success": False,
            "message": f"Failed to reset data: {str(e)}",
        }


# ============================================================================
# SWARM CONTROL ENDPOINTS
# ============================================================================

@router.get("/swarm/status")
async def get_swarm_status():
    """Get the current swarm status."""
    from app.session import get_current_swarm
    swarm = get_current_swarm()
    return {
        "status": swarm.status,
        "is_running": swarm.is_running,
    }


@router.post("/swarm/start")
async def start_swarm():
    """Start or resume the agent swarm."""
    from app.session import get_current_swarm
    swarm = get_current_swarm()
    await swarm.start()
    return {
        "success": True,
        "status": swarm.status,
        "message": "Swarm started",
    }


@router.post("/swarm/stop")
async def stop_swarm():
    """Stop the agent swarm completely."""
    from app.session import get_current_swarm
    swarm = get_current_swarm()
    await swarm.stop()
    return {
        "success": True,
        "status": swarm.status,
        "message": "Swarm stopped",
    }


@router.post("/swarm/pause")
async def pause_swarm():
    """Pause the agent swarm (agents stop taking new work)."""
    from app.session import get_current_swarm
    swarm = get_current_swarm()
    await swarm.pause()
    return {
        "success": True,
        "status": swarm.status,
        "message": "Swarm paused",
    }


@router.post("/swarm/resume")
async def resume_swarm():
    """Resume the agent swarm after pausing."""
    from app.session import get_current_swarm
    swarm = get_current_swarm()
    await swarm.resume()
    return {
        "success": True,
        "status": swarm.status,
        "message": "Swarm resumed",
    }
