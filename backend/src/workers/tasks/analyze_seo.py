"""Celery task for SEO analysis."""

import asyncio
from typing import Any, Optional

from src.config.database import DatabaseConfig
from src.config.logging import get_logger
from src.services.seo_batch_analyzer import create_seo_batch_analyzer
from src.workers.base_task import DatabaseTask
from src.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="analyze_seo_single",
    queue="seo_analysis",
)
def analyze_seo_single_task(self, article_id: int) -> dict[str, Any]:
    """Background task to analyze SEO for a single article.

    Args:
        article_id: Article ID to analyze

    Returns:
        dict: Result with SEO metadata ID and scores
    """
    logger.info(
        "analyze_seo_single_task_started",
        task_id=self.request.id,
        article_id=article_id,
    )

    async def _analyze() -> dict[str, Any]:
        """Async SEO analysis logic."""
        db_config = DatabaseConfig()
        try:
            async with db_config.session() as session:
                analyzer = await create_seo_batch_analyzer(session)
                seo_metadata = await analyzer.analyze_article_by_id(article_id)
                return {
                    "article_id": article_id,
                    "seo_id": seo_metadata.id,
                    "focus_keyword": seo_metadata.focus_keyword,
                    "seo_score": seo_metadata.seo_score,
                    "readability_score": seo_metadata.readability_score,
                    "status": "completed",
                }
        finally:
            await db_config.close()

    try:
        result = asyncio.run(_analyze())

        logger.info(
            "analyze_seo_single_task_completed",
            task_id=self.request.id,
            article_id=article_id,
            seo_score=result["seo_score"],
        )

        return result

    except Exception as e:
        logger.error(
            "analyze_seo_single_task_failed",
            task_id=self.request.id,
            article_id=article_id,
            error=str(e),
            exc_info=True,
        )
        return {
            "article_id": article_id,
            "status": "failed",
            "error": str(e),
        }


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="analyze_seo_batch",
    queue="seo_analysis",
)
def analyze_seo_batch_task(self, limit: Optional[int] = None) -> dict[str, Any]:
    """Background task to analyze SEO for all imported articles.

    Args:
        limit: Optional limit on number of articles to process

    Returns:
        dict: Batch analysis results with counts and errors
    """
    logger.info(
        "analyze_seo_batch_task_started",
        task_id=self.request.id,
        limit=limit,
    )

    async def _analyze_batch() -> dict[str, Any]:
        """Async batch SEO analysis logic."""
        db_config = DatabaseConfig()
        try:
            async with db_config.session() as session:
                analyzer = await create_seo_batch_analyzer(session)
                successful, failed, errors = await analyzer.analyze_imported_articles(limit=limit)
                return {
                    "successful_count": successful,
                    "failed_count": failed,
                    "total_count": successful + failed,
                    "errors": errors,
                    "status": "completed",
                }
        finally:
            await db_config.close()

    try:
        result = asyncio.run(_analyze_batch())

        logger.info(
            "analyze_seo_batch_task_completed",
            task_id=self.request.id,
            successful=result["successful_count"],
            failed=result["failed_count"],
        )

        return result

    except Exception as e:
        logger.error(
            "analyze_seo_batch_task_failed",
            task_id=self.request.id,
            error=str(e),
            exc_info=True,
        )
        return {
            "successful_count": 0,
            "failed_count": 0,
            "total_count": 0,
            "errors": [str(e)],
            "status": "failed",
        }
