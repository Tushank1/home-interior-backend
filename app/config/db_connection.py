from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker,DeclarativeBase
from sqlalchemy import create_engine
from typing import AsyncGenerator
from app.config.settings import settings

# Async database setup
async_engine = create_async_engine(
    settings.database_url_async,
    echo=settings.debug,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600
    )

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

# Sync database setup (for Alembic migration)
sync_engine = create_engine(
    settings.database_url_sync,
    echo=settings.debug,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600
)

SyncSessionLocal = sessionmaker(
    sync_engine,
    autoflush=False,
    autocommit=False
)

class Base(DeclarativeBase):
    pass

# Database Dependency
async def get_db() -> AsyncGenerator[AsyncSession,None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
