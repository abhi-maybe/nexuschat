"""Database connection and session management."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from server.database.models import Base
from config import settings
import logging
import os

logger = logging.getLogger(__name__)


def _normalize_db_url(url: str) -> str:
    """Ensure the URL uses the correct async driver."""
    if url.startswith("postgresql://") and "+" not in url.split("://")[0]:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


def _is_postgres(url: str) -> bool:
    return "postgresql" in url or "postgres://" in url


class DatabaseManager:
    """Manages async SQLAlchemy engine and sessions."""

    def __init__(self):
        self.engine = None
        self.session_factory = None

    async def initialize(self):
        """Set up engine and create tables."""
        db_url = _normalize_db_url(settings.database_url)
        is_pg = _is_postgres(db_url)
        db_type = "PostgreSQL (Supabase)" if is_pg else "SQLite"
        logger.info("Connecting to %s", db_type)

        connect_args = {}
        if not is_pg:
            connect_args["check_same_thread"] = False

        engine_kwargs = {
            "echo": settings.debug,
            "pool_pre_ping": True,
            "connect_args": connect_args,
        }

        if is_pg:
            # Supabase pooler settings — disable prepared statements
            engine_kwargs["pool_size"] = 5
            engine_kwargs["max_overflow"] = 10
            engine_kwargs["connect_args"] = {
                "ssl": "require",
                "statement_cache_size": 0,  # Required for Supabase pooler (PgBouncer)
            }

        self.engine = create_async_engine(db_url, **engine_kwargs)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

        logger.info("Initializing database tables...")
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database ready (%s)", db_type)

    async def close(self):
        if self.engine:
            await self.engine.dispose()

    def get_session(self) -> AsyncSession:
        """Create a new async session."""
        return self.session_factory()
