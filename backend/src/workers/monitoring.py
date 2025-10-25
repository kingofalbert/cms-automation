"""Task monitoring and metrics collection for Celery."""

from typing import Any

from celery.events import Event
from celery.events.state import State

from src.config.logging import get_logger

logger = get_logger(__name__)


class TaskMonitor:
    """Monitor Celery task execution and collect metrics."""

    def __init__(self) -> None:
        """Initialize task monitor."""
        self.state = State()
        self.metrics = {
            "tasks_started": 0,
            "tasks_succeeded": 0,
            "tasks_failed": 0,
            "tasks_retried": 0,
        }

    def on_task_sent(self, event: Event) -> None:
        """Handle task-sent event.

        Args:
            event: Celery event object
        """
        self.state.event(event)
        logger.info(
            "task_sent",
            task_id=event["uuid"],
            task_name=event["name"],
            args=event.get("args"),
            kwargs=event.get("kwargs"),
        )

    def on_task_started(self, event: Event) -> None:
        """Handle task-started event.

        Args:
            event: Celery event object
        """
        self.state.event(event)
        self.metrics["tasks_started"] += 1
        logger.info(
            "task_started",
            task_id=event["uuid"],
            worker=event.get("hostname"),
        )

    def on_task_succeeded(self, event: Event) -> None:
        """Handle task-succeeded event.

        Args:
            event: Celery event object
        """
        self.state.event(event)
        self.metrics["tasks_succeeded"] += 1

        task = self.state.tasks.get(event["uuid"])
        if task:
            logger.info(
                "task_succeeded",
                task_id=event["uuid"],
                task_name=task.name,
                runtime=event.get("runtime"),
                result=event.get("result"),
            )

    def on_task_failed(self, event: Event) -> None:
        """Handle task-failed event.

        Args:
            event: Celery event object
        """
        self.state.event(event)
        self.metrics["tasks_failed"] += 1

        task = self.state.tasks.get(event["uuid"])
        if task:
            logger.error(
                "task_failed",
                task_id=event["uuid"],
                task_name=task.name,
                exception=event.get("exception"),
                traceback=event.get("traceback"),
            )

    def on_task_retried(self, event: Event) -> None:
        """Handle task-retried event.

        Args:
            event: Celery event object
        """
        self.state.event(event)
        self.metrics["tasks_retried"] += 1

        task = self.state.tasks.get(event["uuid"])
        if task:
            logger.warning(
                "task_retried",
                task_id=event["uuid"],
                task_name=task.name,
                exception=event.get("exception"),
            )

    def get_metrics(self) -> dict[str, Any]:
        """Get current metrics.

        Returns:
            dict: Current metrics dictionary
        """
        return {
            **self.metrics,
            "active_tasks": len(
                [t for t in self.state.tasks.values() if t.state == "STARTED"]
            ),
            "pending_tasks": len(
                [t for t in self.state.tasks.values() if t.state == "PENDING"]
            ),
        }


def start_monitoring() -> TaskMonitor:
    """Start task monitoring.

    Returns:
        TaskMonitor: Task monitor instance
    """
    from src.workers.celery_app import celery_app

    monitor = TaskMonitor()

    # Register event handlers
    with celery_app.connection() as connection:
        recv = celery_app.events.Receiver(
            connection,
            handlers={
                "task-sent": monitor.on_task_sent,
                "task-started": monitor.on_task_started,
                "task-succeeded": monitor.on_task_succeeded,
                "task-failed": monitor.on_task_failed,
                "task-retried": monitor.on_task_retried,
            },
        )
        recv.capture(limit=None, timeout=None)

    return monitor
