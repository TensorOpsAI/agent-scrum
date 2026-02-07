from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False}
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def _run_migrations(conn):
    """Run ALTER TABLE migrations for new columns on existing databases."""
    import sqlalchemy as sa

    # Columns to add: (table, column_name, column_type_sql)
    new_columns = [
        ("pipeline_configs", "sub_item_noun", "VARCHAR(50) DEFAULT 'Task'"),
        ("pipeline_configs", "input_noun", "VARCHAR(50) DEFAULT 'PRD'"),
        ("pipeline_configs", "epic_noun", "VARCHAR(50) DEFAULT 'Epic'"),
        ("pipeline_configs", "input_placeholder", "TEXT"),
        ("pipeline_configs", "sub_item_statuses", "JSON"),
        ("stories", "epic_id", "INTEGER REFERENCES epics(id)"),
        ("pipeline_configs", "item_source", "VARCHAR(20) DEFAULT 'internal'"),
    ]

    for table, column, col_type in new_columns:
        try:
            await conn.execute(sa.text(
                f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
            ))
        except Exception:
            # Column already exists – safe to ignore
            pass


async def init_db():
    """Initialize the database and seed default agents."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Run column migrations for existing databases
    async with engine.begin() as conn:
        await _run_migrations(conn)

    # Seed default agents if they don't exist
    from app.db.seed import seed_default_agents
    async with async_session_maker() as db:
        await seed_default_agents(db)
