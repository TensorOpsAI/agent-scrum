from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    from app.session import get_current_session_maker
    maker = get_current_session_maker()
    async with maker() as session:
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


async def init_db(engine: AsyncEngine, session_maker: async_sessionmaker[AsyncSession]):
    """Initialize the database and seed default agents.

    Called by SessionManager when creating a new session.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Run column migrations for existing databases
    async with engine.begin() as conn:
        await _run_migrations(conn)

    # Seed default agents if they don't exist
    from app.db.seed import seed_default_agents
    async with session_maker() as db:
        await seed_default_agents(db)
