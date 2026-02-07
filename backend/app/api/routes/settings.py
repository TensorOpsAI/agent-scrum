"""Settings API - Configuration and control endpoints."""
import os
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.config import get_settings, Settings
from app.db.database import get_db
from app.db.seed import seed_default_agents
from app.agents.swarm import swarm

router = APIRouter(prefix="/api/settings", tags=["settings"])


class APIKeyUpdate(BaseModel):
    api_key: str


class SettingsResponse(BaseModel):
    has_api_key: bool
    simulate_mode: bool
    model: str
    swarm_status: str


# Track simulate mode at runtime (pydantic-settings is cached)
_runtime_simulate_mode: bool | None = None


def get_simulate_mode() -> bool:
    """Get current simulate mode (runtime or from config)."""
    global _runtime_simulate_mode
    if _runtime_simulate_mode is not None:
        return _runtime_simulate_mode
    settings = get_settings()
    return settings.simulate_mode


def set_simulate_mode(enabled: bool):
    """Set simulate mode at runtime."""
    global _runtime_simulate_mode
    _runtime_simulate_mode = enabled


@router.get("", response_model=SettingsResponse)
async def get_current_settings():
    """Get current settings (without exposing the actual API key)."""
    settings = get_settings()
    return SettingsResponse(
        has_api_key=bool(settings.gemini_api_key),
        simulate_mode=get_simulate_mode(),
        model=settings.gemini_model,
        swarm_status=swarm.status,
    )


@router.post("/api-key")
async def update_api_key(data: APIKeyUpdate):
    """Update the Gemini API key at runtime."""
    # Update environment variable
    os.environ["GEMINI_API_KEY"] = data.api_key

    # Clear the settings cache to reload
    get_settings.cache_clear()

    # Disable simulate mode since we now have an API key
    set_simulate_mode(False)

    return {
        "success": True,
        "message": "API key updated successfully",
        "simulate_mode": False,
    }


@router.delete("/api-key")
async def clear_api_key():
    """Clear the Gemini API key and switch to simulation mode."""
    # Clear environment variable
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]

    # Clear the settings cache to reload
    get_settings.cache_clear()

    # Enable simulate mode since we no longer have an API key
    set_simulate_mode(True)

    return {
        "success": True,
        "message": "API key cleared, switched to simulation mode",
        "simulate_mode": True,
    }


@router.post("/simulate-mode")
async def toggle_simulate_mode(enabled: bool = True):
    """Toggle simulation mode on/off."""
    set_simulate_mode(enabled)
    return {
        "success": True,
        "simulate_mode": enabled,
    }


@router.post("/reset")
async def reset_all_data(db: AsyncSession = Depends(get_db)):
    """Reset the board and swarm. Preserves settings, API key, and pipeline config."""
    try:
        # Stop the swarm first
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
    return {
        "status": swarm.status,
        "is_running": swarm.is_running,
    }


@router.post("/swarm/start")
async def start_swarm():
    """Start or resume the agent swarm."""
    await swarm.start()
    return {
        "success": True,
        "status": swarm.status,
        "message": "Swarm started",
    }


@router.post("/swarm/stop")
async def stop_swarm():
    """Stop the agent swarm completely."""
    await swarm.stop()
    return {
        "success": True,
        "status": swarm.status,
        "message": "Swarm stopped",
    }


@router.post("/swarm/pause")
async def pause_swarm():
    """Pause the agent swarm (agents stop taking new work)."""
    await swarm.pause()
    return {
        "success": True,
        "status": swarm.status,
        "message": "Swarm paused",
    }


@router.post("/swarm/resume")
async def resume_swarm():
    """Resume the agent swarm after pausing."""
    await swarm.resume()
    return {
        "success": True,
        "status": swarm.status,
        "message": "Swarm resumed",
    }
