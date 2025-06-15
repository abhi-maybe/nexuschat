"""Database connection and session management."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from server.database.models import Base
from config import settings


class DatabaseManager:
    """Manages async SQLAlchemy engine and sessions."""

    def __init__(self):
        self.engine = None
        self.session_factory = None

    async def initialize(self):
        """Create engine and tables."""
        db_url = settings.database_url
        if db_url.startswith("sqlite:///"):
            db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")

        self.engine = create_async_engine(db_url, echo=settings.debug)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self):
        if self.engine:
            await self.engine.dispose()

    def get_session(self) -> AsyncSession:
        return self.session_factory()
