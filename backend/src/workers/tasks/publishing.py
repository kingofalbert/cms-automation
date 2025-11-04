"""Celery tasks for publishing workflow orchestration."""

from __future__ import annotations

import asyncio
from typing import Any

from src.config import get_logger
from src.services.publishing import PublishingOrchestrator
from src.workers.celery_app import celery_app

logger = get_logger(__name__)


def _run_publish_workflow(
    publish_task_id: int,
    article_id: int,
    provider: str,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Helper to execute orchestrator in a synchronous Celery task."""
    orchestrator = PublishingOrchestrator()
    return asyncio.run(
        orchestrator.publish_article(
            publish_task_id=publish_task_id,
            article_id=article_id,
            provider=provider,
            options=options or {},
        )
    )


@celery_app.task(
    name="publishing.submit",
    bind=True,
    max_retries=0,
)
def publish_article_task(
    self,
    publish_task_id: int,
    article_id: int,
    provider: str,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Celery entrypoint for new publishing tasks."""
    logger.info(
        "publishing_task_started",
        celery_task_id=self.request.id,
        publish_task_id=publish_task_id,
        article_id=article_id,
        provider=provider,
    )

    try:
        result = _run_publish_workflow(
            publish_task_id=publish_task_id,
            article_id=article_id,
            provider=provider,
            options=options,
        )
        logger.info(
            "publishing_task_succeeded",
            celery_task_id=self.request.id,
            publish_task_id=publish_task_id,
            article_id=article_id,
            provider=provider,
        )
        return result
    except Exception as exc:
        logger.error(
            "publishing_task_failed",
            celery_task_id=self.request.id,
            publish_task_id=publish_task_id,
            article_id=article_id,
            provider=provider,
            error=str(exc),
            exc_info=True,
        )
        raise


@celery_app.task(
    name="publishing.retry",
    bind=True,
    max_retries=0,
)
def retry_publish_article_task(
    self,
    publish_task_id: int,
    article_id: int,
    provider: str,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Celery entrypoint for retrying existing publishing tasks."""
    logger.info(
        "publishing_task_retry_started",
        celery_task_id=self.request.id,
        publish_task_id=publish_task_id,
        article_id=article_id,
        provider=provider,
    )

    try:
        result = _run_publish_workflow(
            publish_task_id=publish_task_id,
            article_id=article_id,
            provider=provider,
            options=options,
        )
        logger.info(
            "publishing_task_retry_succeeded",
            celery_task_id=self.request.id,
            publish_task_id=publish_task_id,
            article_id=article_id,
            provider=provider,
        )
        return result
    except Exception as exc:
        logger.error(
            "publishing_task_retry_failed",
            celery_task_id=self.request.id,
            publish_task_id=publish_task_id,
            article_id=article_id,
            provider=provider,
            error=str(exc),
            exc_info=True,
        )
        raise
