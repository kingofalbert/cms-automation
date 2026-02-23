"""Celery application configuration."""

from celery import Celery
from celery.signals import setup_logging, worker_ready

from src.config import get_settings
from src.config import setup_logging as setup_app_logging

settings = get_settings()

# Create Celery application
celery_app = Celery(
    "cms_automation",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery from settings
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=settings.CELERY_ENABLE_UTC,
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
    worker_max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,  # Enable extended result format
    # Task routing
    task_routes={
        "src.workers.tasks.generate_article.*": {"queue": "article_generation"},
        "src.workers.tasks.publish_scheduled.*": {"queue": "publishing"},
        "src.workers.tasks.publishing.*": {"queue": "publishing"},
        "pipeline.auto_publish": {"queue": "publishing"},
    },
    # Task execution settings
    task_acks_late=True,  # Acknowledge after execution
    task_reject_on_worker_lost=True,  # Reject tasks if worker dies
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    # Fast-fail when broker (Redis) is unreachable so the API can fall back
    # to synchronous execution quickly instead of waiting ~20s.
    broker_connection_timeout=2,
    broker_connection_retry=False,
)

# Auto-discover tasks from all modules
celery_app.autodiscover_tasks(
    [
        "src.workers.tasks",
    ]
)


@setup_logging.connect
def setup_celery_logging(**kwargs) -> None:
    """Setup custom logging for Celery workers."""
    setup_app_logging()


@worker_ready.connect
def on_worker_ready(**kwargs) -> None:
    """Log when worker is ready."""
    from src.config.logging import get_logger

    logger = get_logger(__name__)
    logger.info("celery_worker_ready", settings_environment=settings.ENVIRONMENT)


# Define task base classes and utilities
from celery import Task


class DatabaseTask(Task):
    """Base task class with database session management."""

    _db_config = None

    @property
    def db_config(self):
        """Lazy load database configuration."""
        if self._db_config is None:
            from src.config.database import get_db_config

            self._db_config = get_db_config()
        return self._db_config


# Export for convenience
def get_celery_app() -> Celery:
    """Get the Celery application instance.

    Returns:
        Celery: Celery application
    """
    return celery_app
