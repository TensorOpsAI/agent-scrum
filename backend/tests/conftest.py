import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.config import get_settings
from app.db.seed import seed_default_agents, DEFAULT_AGENTS
from app.db.models import PipelineConfig

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Override settings for tests
settings = get_settings()

# Verify default agents are defined
assert len(DEFAULT_AGENTS) > 0, "No default agents defined"


@pytest.fixture(scope="session")
def event_loop_policy():
    """Create an event loop policy for the session."""
    return asyncio.get_event_loop_policy()


@pytest.fixture(scope="function")
async def test_engine():
    """Create a test database engine and seed default agents."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default agents for tests
    test_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with test_session_maker() as session:
        await seed_default_agents(session)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
async def test_board(test_session: AsyncSession) -> PipelineConfig:
    """Return the default board that was seeded during engine setup."""
    result = await test_session.execute(
        select(PipelineConfig).limit(1)
    )
    board = result.scalar_one()
    return board


@pytest.fixture(scope="function")
async def client(test_engine) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with a test database."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async def override_get_db():
        async with async_session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_prd():
    """Sample PRD content for testing."""
    return """
# Feature: User Authentication

## Overview
Implement a secure user authentication system for the application.

## Requirements
- Users should be able to sign up with email and password
- Users should be able to log in with their credentials
- Passwords should be securely hashed
- Sessions should expire after 24 hours

## Acceptance Criteria
- User can register with valid email
- User cannot register with duplicate email
- Login returns a session token
- Invalid credentials return an error
"""


@pytest.fixture
def sample_story_data():
    """Sample story data for testing."""
    return {
        "title": "Implement User Login",
        "description": "As a user, I want to log in to my account so that I can access my data",
        "acceptance_criteria": "- User can enter email and password\n- Valid credentials grant access\n- Invalid credentials show error",
        "priority": 1
    }


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        "title": "Create login API endpoint",
        "description": "Implement POST /api/auth/login endpoint",
    }
