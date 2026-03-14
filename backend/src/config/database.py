"""Database connection configuration and session management."""

import asyncio
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import TypeVar
from uuid import uuid4

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config.logging import get_logger
from src.config.settings import get_settings

logger = get_logger(__name__)

T = TypeVar("T")


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

            # Ensure SSL is enabled (required for Supabase)
            if "ssl=" not in db_url and "sslmode=" not in db_url:
                separator = "&" if "?" in db_url else "?"
                db_url = f"{db_url}{separator}ssl=require"

            pool_size = self.settings.DATABASE_POOL_SIZE
            max_overflow = self.settings.DATABASE_MAX_OVERFLOW
            pool_recycle = self.settings.DATABASE_POOL_RECYCLE

            engine_kwargs = {
                "echo": self.settings.LOG_LEVEL == "DEBUG",
                # QueuePool with pre_ping: reuses connections (avoids per-request
                # initialization cost that triggers ConnectionDoesNotExistError
                # with Supavisor Transaction Mode) and validates them before use.
                "pool_pre_ping": True,
                "pool_size": pool_size,
                "max_overflow": max_overflow,
                "pool_recycle": pool_recycle,
                "pool_timeout": self.settings.DATABASE_POOL_TIMEOUT,
                "connect_args": {
                    "statement_cache_size": 0,
                    "prepared_statement_cache_size": 0,
                    "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
                    "command_timeout": 60,
                    "server_settings": {
                        "jit": "off",
                    },
                },
            }

            self._engine = create_async_engine(db_url, **engine_kwargs)

            # Pool event listeners for observability
            sync_engine = self._engine.sync_engine

            @event.listens_for(sync_engine, "connect")
            def _on_connect(dbapi_conn, connection_record):
                logger.debug("db_pool_connect", id=id(dbapi_conn))

            @event.listens_for(sync_engine, "checkout")
            def _on_checkout(dbapi_conn, connection_record, connection_proxy):
                logger.debug("db_pool_checkout", id=id(dbapi_conn))

            @event.listens_for(sync_engine, "checkin")
            def _on_checkin(dbapi_conn, connection_record):
                logger.debug("db_pool_checkin", id=id(dbapi_conn))

            logger.info(
                "database_engine_created",
                pool_class="QueuePool",
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_recycle=pool_recycle,
                pool_pre_ping=True,
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

    async def execute_with_retry(
        self,
        operation: Callable[..., T],
        max_attempts: int = 3,
    ) -> T:
        """Execute a database operation with retry on transient connection errors.

        Args:
            operation: An async callable that receives an AsyncSession and returns a result.
            max_attempts: Maximum number of attempts (default 3).

        Returns:
            The result of the operation.

        Example:
            async def fetch_articles(session):
                result = await session.execute(select(Article))
                return result.scalars().all()

            articles = await db_config.execute_with_retry(fetch_articles)
        """
        backoff_delays = [0.5, 1.0, 2.0]
        last_exc: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                async with self.session() as session:
                    return await operation(session)
            except Exception as exc:
                if attempt >= max_attempts or not self._is_transient(exc):
                    raise
                last_exc = exc
                delay = backoff_delays[min(attempt - 1, len(backoff_delays) - 1)]
                logger.warning(
                    "db_transient_error_retrying",
                    attempt=attempt,
                    max_attempts=max_attempts,
                    delay=delay,
                    error_type=type(exc).__name__,
                    error=str(exc),
                )
                await asyncio.sleep(delay)

        # Should not reach here, but satisfy type checker
        raise last_exc  # type: ignore[misc]

    @staticmethod
    def _is_transient(exc: BaseException) -> bool:
        """Check if an exception is a transient connection error worth retrying."""
        transient_names = {
            "ConnectionDoesNotExistError",
            "InterfaceError",
            "ConnectionRefusedError",
            "ConnectionResetError",
            "TimeoutError",
        }
        # Walk the cause chain
        current: BaseException | None = exc
        while current is not None:
            if type(current).__name__ in transient_names:
                return True
            current = current.__cause__
        return False


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
