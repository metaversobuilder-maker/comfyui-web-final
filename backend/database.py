from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
import sys
from pathlib import Path

# Add parent to path
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

from config import settings

# Async engine for FastAPI (SQLite)
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)

# Sync engine for migrations/initial setup (SQLite)
sync_engine = create_engine(
    settings.database_url_sync,
    echo=settings.debug,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Sync session factory
SessionLocal = sessionmaker(
    sync_engine,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db():
    """Dependency for getting async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
