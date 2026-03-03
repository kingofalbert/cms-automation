"""Periodic maintenance tasks for database cleanup and health checks."""

from __future__ import annotations

import asyncio

from src.config import get_logger
from src.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="src.workers.tasks.maintenance.cleanup_old_tasks")
def cleanup_old_tasks() -> dict:
    """Clean up old completed Celery task results from Redis."""
    logger.info("cleanup_old_tasks_started")
    # Celery handles result expiry via result_expires config; this is a no-op placeholder
    return {"status": "ok"}


@celery_app.task(name="src.workers.tasks.maintenance.health_check")
def health_check() -> dict:
    """Periodic health check — verifies DB connectivity."""

    async def _check() -> dict:
        from sqlalchemy import text

        from src.config.database import get_db_config

        db_config = get_db_config()
        try:
            async with db_config.session() as session:
                await session.execute(text("SELECT 1"))
            return {"status": "healthy", "database": "ok"}
        except Exception as exc:
            logger.error("health_check_db_failed", error=str(exc))
            return {"status": "degraded", "database": str(type(exc).__name__)}

    return asyncio.run(_check())


@celery_app.task(name="src.workers.tasks.maintenance.cleanup_published_items")
def cleanup_published_items() -> dict:
    """Scheduled cleanup: free DB space for published items that missed auto-cleanup.

    Finds WorklistItems with status=PUBLISHED that still have large content fields,
    and runs cleanup on each. Also cleans FAILED items older than 7 days.
    """

    async def _cleanup() -> dict:
        from datetime import datetime, timedelta

        from sqlalchemy import or_, select

        from src.config.database import get_db_config
        from src.models import WorklistItem, WorklistStatus
        from src.services.worklist.auto_publish import AutoPublishService

        db_config = get_db_config()
        cleaned = 0
        errors = 0
        total_freed = 0

        async with db_config.session() as session:
            # Find published items that still have content (missed cleanup)
            stmt = select(WorklistItem).where(
                WorklistItem.status == WorklistStatus.PUBLISHED,
                WorklistItem.content != "",
                WorklistItem.content.isnot(None),
            ).limit(50)  # Process in batches
            result = await session.execute(stmt)
            items = result.scalars().all()

            for item in items:
                try:
                    service = AutoPublishService(session)
                    freed = await service.cleanup_published_item(item.id)
                    total_freed += freed
                    cleaned += 1
                except Exception as exc:
                    logger.warning(
                        "scheduled_cleanup_item_failed",
                        worklist_item_id=item.id,
                        error=str(exc),
                    )
                    errors += 1

            # Also clean up FAILED items older than 7 days (delete large fields only)
            cutoff = datetime.utcnow() - timedelta(days=7)
            stmt_failed = select(WorklistItem).where(
                WorklistItem.status == WorklistStatus.FAILED,
                WorklistItem.updated_at < cutoff,
                or_(
                    WorklistItem.content != "",
                    WorklistItem.raw_html.isnot(None),
                ),
            ).limit(50)
            result_failed = await session.execute(stmt_failed)
            failed_items = result_failed.scalars().all()

            for item in failed_items:
                try:
                    # For failed items, just clear the large fields directly
                    if item.content:
                        total_freed += len(item.content.encode("utf-8", errors="ignore"))
                        item.content = ""
                    if item.raw_html:
                        total_freed += len(item.raw_html.encode("utf-8", errors="ignore"))
                        item.raw_html = None
                    if item.notes:
                        item.notes = []
                    session.add(item)
                    cleaned += 1
                except Exception as exc:
                    logger.warning(
                        "scheduled_cleanup_failed_item_error",
                        worklist_item_id=item.id,
                        error=str(exc),
                    )
                    errors += 1

            await session.commit()

        logger.info(
            "scheduled_cleanup_completed",
            cleaned=cleaned,
            errors=errors,
            total_freed_bytes=total_freed,
        )
        return {
            "status": "ok",
            "cleaned": cleaned,
            "errors": errors,
            "freed_bytes_estimate": total_freed,
        }

    return asyncio.run(_cleanup())
