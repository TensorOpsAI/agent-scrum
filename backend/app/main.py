"""
Agent Scrum - AI Multi-Agent Demo

Main FastAPI application for multi-agent collaboration on software development.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.database import init_db
from app.api.routes import stories, tasks, agents, prd, workflow, chat, agent_management, pipeline
from app.api.routes import settings as settings_routes
from app.api.websocket.manager import manager
from app.agents.swarm import swarm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_db()
    await swarm.start()
    print("[Startup] Agent Scrum started with LangGraph agents")
    yield
    # Shutdown
    await swarm.stop()


app = FastAPI(
    title="Agent Scrum - AI Multi-Agent Demo",
    description="Multi-agent collaboration on software development workflow using LangGraph",
    version="0.2.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stories.router)
app.include_router(tasks.router)
app.include_router(agents.router)
app.include_router(prd.router)
app.include_router(workflow.router)
app.include_router(chat.router)
app.include_router(settings_routes.router)
app.include_router(agent_management.router)
app.include_router(pipeline.router)


@app.get("/")
async def root():
    return {
        "name": "Agent Scrum",
        "version": "0.2.0",
        "description": "AI Multi-Agent Demo - Multi-agent collaboration platform using LangGraph",
        "agents": [
            "product_owner",
            "tech_lead",
            "developer",
            "code_reviewer",
            "qa",
            "scrum_master",
        ]
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Could handle client-side events here if needed
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
