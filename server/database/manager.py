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
    # Supabase gives postgresql:// — convert to async driver
    if url.startswith("postgresql://") and "+" not in url.split("://")[0]:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


class DatabaseManager:
    """Manages async SQLAlchemy engine and sessions."""

    def __init__(self):
        self.engine = None
        self.session_factory = None

    async def initialize(self):
        """Set up engine and create tables."""
        db_url = _normalize_db_url(settings.database_url)
        db_type = "PostgreSQL (Supabase)" if "asyncpg" in db_url else "SQLite"
        logger.info("Connecting to %s", db_type)

        connect_args = {}
        if "sqlite" in db_url:
            connect_args["check_same_thread"] = False

        self.engine = create_async_engine(
            db_url,
            echo=settings.debug,
            pool_pre_ping=True,
            pool_size=5 if "asyncpg" in db_url else 0,
            max_overflow=10 if "asyncpg" in db_url else 0,
            connect_args=connect_args,
        )
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
