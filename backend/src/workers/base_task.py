"""Base task classes with retry logic and error handling."""

from typing import Any

from celery import Task

from src.config.logging import get_logger
from src.config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


class RetryableTask(Task):
    """Base task class with automatic retry logic."""

    autoretry_for = (Exception,)
    retry_kwargs = {
        "max_retries": settings.MAX_RETRIES,
        "countdown": settings.RETRY_DELAY,
    }
    retry_backoff = True
    retry_backoff_max = 600  # Maximum 10 minutes
    retry_jitter = True

    def on_failure(
        self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any
    ) -> None:
        """Handle task failure.

        Args:
            exc: Exception that caused the failure
            task_id: Unique task ID
            args: Task positional arguments
            kwargs: Task keyword arguments
            einfo: Exception info object
        """
        logger.error(
            "task_failed",
            task_id=task_id,
            task_name=self.name,
            exception=str(exc),
            args=args,
            kwargs=kwargs,
            exc_info=True,
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(
        self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any
    ) -> None:
        """Handle task retry.

        Args:
            exc: Exception that caused the retry
            task_id: Unique task ID
            args: Task positional arguments
            kwargs: Task keyword arguments
            einfo: Exception info object
        """
        logger.warning(
            "task_retry",
            task_id=task_id,
            task_name=self.name,
            exception=str(exc),
            retry_count=self.request.retries,
            max_retries=settings.MAX_RETRIES,
        )
        super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict) -> None:
        """Handle task success.

        Args:
            retval: Task return value
            task_id: Unique task ID
            args: Task positional arguments
            kwargs: Task keyword arguments
        """
        logger.info(
            "task_completed",
            task_id=task_id,
            task_name=self.name,
            duration_ms=self.request.duration * 1000 if self.request.duration else None,
        )
        super().on_success(retval, task_id, args, kwargs)


class DatabaseTask(RetryableTask):
    """Base task class with database session management."""

    _db_config = None

    @property
    def db_config(self):
        """Lazy load database configuration."""
        if self._db_config is None:
            from src.config.database import get_db_config

            self._db_config = get_db_config()
        return self._db_config

    async def get_session(self):
        """Get database session for task execution.

        Yields:
            AsyncSession: Database session
        """
        async with self.db_config.session() as session:
            yield session


class RateLimitedTask(RetryableTask):
    """Base task class with rate limiting."""

    rate_limit = "10/m"  # 10 tasks per minute

    def apply_async(self, *args, **kwargs):
        """Apply rate limiting before task execution."""
        return super().apply_async(*args, **kwargs)
