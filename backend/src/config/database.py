"""Database connection configuration and session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool

from src.config.logging import get_logger
from src.config.settings import get_settings

logger = get_logger(__name__)


class DatabaseConfig:
    """Database configuration and connection management."""

    def __init__(self) -> None:
        """Initialize database configuration."""
        self.settings = get_settings()
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def get_engine(self) -> AsyncEngine:
        """Get or create the database engine.

        Returns:
            AsyncEngine: SQLAlchemy async engine
        """
        if self._engine is None:
            # Convert postgresql:// to postgresql+asyncpg://
            db_url = str(self.settings.DATABASE_URL)
            if db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

            # For async engines, only use NullPool in test mode
            # Default async pool will be used in non-test environments
            engine_kwargs = {
                "echo": self.settings.LOG_LEVEL == "DEBUG",
                "pool_size": self.settings.DATABASE_POOL_SIZE,
                "max_overflow": self.settings.DATABASE_MAX_OVERFLOW,
                "pool_timeout": self.settings.DATABASE_POOL_TIMEOUT,
                "pool_recycle": self.settings.DATABASE_POOL_RECYCLE,
                "pool_pre_ping": True,  # Verify connections before using
            }

            if self.settings.ENVIRONMENT == "test":
                engine_kwargs["poolclass"] = NullPool

            self._engine = create_async_engine(db_url, **engine_kwargs)

            logger.info(
                "database_engine_created",
                pool_size=self.settings.DATABASE_POOL_SIZE,
                max_overflow=self.settings.DATABASE_MAX_OVERFLOW,
                environment=self.settings.ENVIRONMENT,
            )

        return self._engine

    def get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get or create the session factory.

        Returns:
            async_sessionmaker: Session factory for creating database sessions
        """
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                bind=self.get_engine(),
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

            logger.info("database_session_factory_created")

        return self._session_factory

    async def close(self) -> None:
        """Close database connections and dispose of the engine."""
        if self._engine is not None:
            await self._engine.dispose()
            logger.info("database_engine_disposed")
            self._engine = None
            self._session_factory = None

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Create a database session context manager.

        Yields:
            AsyncSession: Database session

        Example:
            async with db_config.session() as session:
                result = await session.execute(select(Article))
        """
        session_factory = self.get_session_factory()
        session = session_factory()

        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Global database configuration instance
_db_config: DatabaseConfig | None = None


def get_db_config() -> DatabaseConfig:
    """Get the global database configuration instance.

    Returns:
        DatabaseConfig: Database configuration singleton
    """
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
    return _db_config


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to inject database sessions.

    Yields:
        AsyncSession: Database session

    Example:
        @app.get("/articles")
        async def get_articles(session: AsyncSession = Depends(get_session)):
            result = await session.execute(select(Article))
            return result.scalars().all()
    """
    db_config = get_db_config()
    async with db_config.session() as session:
        yield session


# Alias for backward compatibility
get_async_session = get_session
