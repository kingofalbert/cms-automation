"""Celery task for the auto-publish pipeline (GAS orchestrator)."""

from __future__ import annotations

import asyncio
from typing import Any

from src.config import get_logger
from src.workers.celery_app import celery_app

logger = get_logger(__name__)


def _run_auto_publish(
    google_doc_url: str,
    sheet_row: int | None = None,
    requester: str = "gas-automation",
) -> dict[str, Any]:
    """Execute the auto-publish pipeline synchronously for Celery."""
    from src.config.database import get_db_config
    from src.services.worklist.auto_publish import AutoPublishService

    async def _inner() -> dict[str, Any]:
        db_config = get_db_config()
        async with db_config.session() as session:
            service = AutoPublishService(session)
            return await service.process_google_doc(
                google_doc_url=google_doc_url,
                sheet_row=sheet_row,
                requester=requester,
            )

    return asyncio.run(_inner())


@celery_app.task(
    name="pipeline.auto_publish",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def auto_publish_task(
    self,
    google_doc_url: str,
    sheet_row: int | None = None,
    requester: str = "gas-automation",
) -> dict[str, Any]:
    """Celery entrypoint for the auto-publish pipeline."""
    logger.info(
        "auto_publish_task_started",
        celery_task_id=self.request.id,
        google_doc_url=google_doc_url,
        sheet_row=sheet_row,
    )

    try:
        result = _run_auto_publish(
            google_doc_url=google_doc_url,
            sheet_row=sheet_row,
            requester=requester,
        )
        logger.info(
            "auto_publish_task_succeeded",
            celery_task_id=self.request.id,
            status=result.get("status"),
            wordpress_draft_url=result.get("wordpress_draft_url"),
        )
        return result
    except Exception as exc:
        logger.error(
            "auto_publish_task_failed",
            celery_task_id=self.request.id,
            google_doc_url=google_doc_url,
            error=str(exc),
            exc_info=True,
        )
        raise self.retry(exc=exc)
