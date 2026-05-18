"""
PostgreSQL connection management via SQLAlchemy (asyncio) and Psycopg 3.
Manages engine initialization and session generation during FastAPI lifespan.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.config import get_settings

# Base class for all declarative SQLAlchemy models to inherit from
Base = declarative_base()

# Module-level references — initialized inside the connect_db lifespan function
_engine = None
_session_factory = None


async def connect_db() -> None:
    """
    Initialize the asynchronous PostgreSQL Engine and Session Factory.
    Equivalency map: Replaces `init_beanie` and `AsyncIOMotorClient`.
    """
    global _engine, _session_factory
    settings = get_settings()

    # Create the async database engine using the modern psycopg driver.
    # pool_pre_ping ensures dead connections are dropped gracefully before executing queries.
    _engine = create_async_engine(
        settings.DATABASE_URL,  # e.g. postgresql+psycopg://user:pass@localhost:5432/antifarm
        echo=False,             # Set to True if you want to print all raw generated SQL statements
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

    # Build the isolated session maker factory
    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Stops SQLAlchemy from expiring attributes after db commits
        autocommit=False,
        autoflush=False
    )

    # In development/competition mode, you can optionally auto-generate tables right here:
    # async with _engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)


async def disconnect_db() -> None:
    """
    Gracefully tear down the connection pool and close all backend connections.
    Equivalency map: Replaces `_client.close()`.
    """
    global _engine, _session_factory
    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None


def get_engine():
    """Returns the underlying SQLAlchemy async engine."""
    if _engine is None:
        raise RuntimeError("Database engine not initialized. Call connect_db() first.")
    return _engine


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI Dependency Injector. Yields an active asynchronous session.
    Automatically handles execution transactions, rollback mechanisms on error, 
    and closure context management.
    
    Usage in resource controllers:
        @router.get("/")
        async def read_data(db: AsyncSession = Depends(get_db)):
    """
    if _session_factory is None:
        raise RuntimeError("Session factory not initialized. Call connect_db() first.")

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()  # Commits transactions automatically upon route success
        except Exception:
            await session.rollback() # Rolls back modifications safely if an error cracks open
            raise
        finally:
            await session.close()   # Destroys session instantly to clear connection pooling space