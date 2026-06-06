"""Database connection and session management."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from server.database.models import Base
from config import settings
import logging
import os
import tempfile

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


def _sqlite_fallback_url() -> str:
    """Generate a SQLite URL for fallback."""
    if os.environ.get("VERCEL"):
        db_path = os.path.join(tempfile.gettempdir(), "nexuschat.db")
    else:
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "nexuschat.db")
    return f"sqlite+aiosqlite:///{db_path}"


class DatabaseManager:
    """Manages async SQLAlchemy engine and sessions."""

    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.db_type = "unknown"

    async def initialize(self):
        """Set up engine and create tables. Tries PostgreSQL first, falls back to SQLite."""
        db_url = _normalize_db_url(settings.database_url)
        is_pg = _is_postgres(db_url)

        if is_pg:
            try:
                await self._init_postgres(db_url)
                self.db_type = "PostgreSQL (Supabase)"
                logger.info("Connected to PostgreSQL (Supabase)")
                return
            except Exception as e:
                logger.error("PostgreSQL connection failed: %s — falling back to SQLite", e)
                db_url = _sqlite_fallback_url()

        await self._init_sqlite(db_url)
        self.db_type = "SQLite"
        logger.info("Connected to SQLite")

    async def _init_postgres(self, db_url: str):
        """Initialize PostgreSQL engine."""
        self.engine = create_async_engine(
            db_url,
            echo=settings.debug,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            connect_args={
                "ssl": "require",
                "statement_cache_size": 0,  # Required for PgBouncer/Supavisor
            },
        )
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await self._ensure_columns(conn)

    async def _init_sqlite(self, db_url: str):
        """Initialize SQLite engine."""
        self.engine = create_async_engine(
            db_url,
            echo=settings.debug,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False},
        )
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def _ensure_columns(self, conn):
        """Add missing columns to existing tables (safe schema migration)."""
        columns_to_ensure = [
            ("user_settings", "openrouter_api_key", "VARCHAR(256) DEFAULT ''"),
            ("user_settings", "xiaomi_api_key", "VARCHAR(256) DEFAULT ''"),
            ("user_settings", "groq_api_key", "VARCHAR(256) DEFAULT ''"),
            ("user_settings", "deepseek_api_key", "VARCHAR(256) DEFAULT ''"),
            ("messages", "parent_id", "INTEGER"),
        ]
        for table, column, col_type in columns_to_ensure:
            try:
                await conn.execute(
                    text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type}")
                )
                logger.info("Ensured column %s.%s exists", table, column)
            except Exception as e:
                logger.debug("Column check %s.%s: %s", table, column, e)

    async def close(self):
        if self.engine:
            await self.engine.dispose()

    def get_session(self) -> AsyncSession:
        """Create a new async session."""
        return self.session_factory()
