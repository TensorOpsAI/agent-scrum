"""
Session Manager - Per-user session isolation via contextvars.

Each session gets its own in-memory SQLite DB, swarm, executor, and A2A router.
Sessions are reaped after 30 minutes of inactivity.
"""
import asyncio
import logging
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Context variables — threaded implicitly through all async code
# ---------------------------------------------------------------------------
_current_session: ContextVar["UserSession"] = ContextVar("_current_session")
_current_api_key: ContextVar[Optional[str]] = ContextVar("_current_api_key", default=None)


# ---------------------------------------------------------------------------
# UserSession dataclass
# ---------------------------------------------------------------------------
@dataclass
class UserSession:
    id: str
    engine: AsyncEngine
    session_maker: async_sessionmaker[AsyncSession]
    swarm: object = field(default=None)          # ScrumSwarm (lazy)
    executor: object = field(default=None)       # AgentExecutor (lazy)
    a2a_router: object = field(default=None)     # A2ARouter (lazy)
    simulate_mode: bool = True
    swarm_active: bool = False
    last_activity: float = field(default_factory=time.time)

    def touch(self):
        self.last_activity = time.time()


# ---------------------------------------------------------------------------
# SessionManager
# ---------------------------------------------------------------------------
SESSION_TTL = 30 * 60  # 30 minutes


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, UserSession] = {}
        self._lock = asyncio.Lock()
        self._reaper_task: Optional[asyncio.Task] = None

    async def get_or_create(self, session_id: str) -> UserSession:
        async with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.touch()
                return session

        # Create outside the lock to avoid holding it during IO
        session = await self._create_session(session_id)
        async with self._lock:
            # Double-check (another request may have created it)
            if session_id in self._sessions:
                # Dispose the one we just created
                await session.engine.dispose()
                session = self._sessions[session_id]
                session.touch()
                return session
            self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[UserSession]:
        return self._sessions.get(session_id)

    async def destroy(self, session_id: str):
        async with self._lock:
            session = self._sessions.pop(session_id, None)
        if session:
            await self._teardown(session)

    async def destroy_all(self):
        async with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for s in sessions:
            await self._teardown(s)

    # -- Reaper --------------------------------------------------------------

    async def start_reaper(self):
        if self._reaper_task is None:
            self._reaper_task = asyncio.create_task(self._reaper_loop())

    async def stop_reaper(self):
        if self._reaper_task:
            self._reaper_task.cancel()
            try:
                await self._reaper_task
            except asyncio.CancelledError:
                pass
            self._reaper_task = None

    async def _reaper_loop(self):
        while True:
            await asyncio.sleep(60)
            now = time.time()
            to_reap: list[str] = []
            async with self._lock:
                for sid, sess in self._sessions.items():
                    if now - sess.last_activity > SESSION_TTL:
                        to_reap.append(sid)
            for sid in to_reap:
                logger.info(f"[Session] Reaping idle session {sid}")
                await self.destroy(sid)

    # -- Internal helpers ----------------------------------------------------

    async def _create_session(self, session_id: str) -> UserSession:
        engine = create_async_engine(
            "sqlite+aiosqlite://",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        # Create tables + seed
        from app.db.database import Base, _run_migrations
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with engine.begin() as conn:
            await _run_migrations(conn)
        from app.db.seed import seed_default_agents
        async with maker() as db:
            await seed_default_agents(db)

        # Lazy components
        from app.agents.executor import AgentExecutor
        from app.agents.swarm.graph import ScrumSwarm
        from app.a2a.router import A2ARouter

        exe = AgentExecutor()
        swarm = ScrumSwarm(session_id=session_id)
        router = A2ARouter()

        session = UserSession(
            id=session_id,
            engine=engine,
            session_maker=maker,
            swarm=swarm,
            executor=exe,
            a2a_router=router,
        )
        logger.info(f"[Session] Created session {session_id}")
        return session

    async def _teardown(self, session: UserSession):
        try:
            if session.swarm:
                await session.swarm.stop()
        except Exception:
            pass
        try:
            await session.engine.dispose()
        except Exception:
            pass
        logger.info(f"[Session] Destroyed session {session.id}")


# Singleton
session_manager = SessionManager()


# ---------------------------------------------------------------------------
# Context helpers — used everywhere to get session-scoped objects
# ---------------------------------------------------------------------------

def get_current_session() -> UserSession:
    return _current_session.get()


def get_current_session_maker() -> async_sessionmaker[AsyncSession]:
    return get_current_session().session_maker


def get_current_api_key() -> Optional[str]:
    return _current_api_key.get()


def get_current_executor():
    return get_current_session().executor


def get_current_swarm():
    return get_current_session().swarm


def get_current_a2a_router():
    return get_current_session().a2a_router


def is_swarm_active() -> bool:
    try:
        return get_current_session().swarm_active
    except LookupError:
        return False


def set_swarm_active(active: bool):
    try:
        get_current_session().swarm_active = active
    except LookupError:
        pass
