"""Celery task for article generation."""

from src.config.database import get_db_config
from src.config.logging import get_logger
from src.services.article_generator import create_article_generator
from src.workers.base_task import DatabaseTask
from src.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="generate_article",
    queue="article_generation",
)
def generate_article_task(self, topic_request_id: int) -> dict:
    """Background task to generate article from topic request.

    Args:
        topic_request_id: TopicRequest ID to process

    Returns:
        dict: Result with article_id and status

    Raises:
        Exception: If generation fails after retries
    """
    import asyncio
    import nest_asyncio

    # Allow nested event loops (for Celery + asyncio)
    nest_asyncio.apply()

    logger.info(
        "generate_article_task_started",
        task_id=self.request.id,
        topic_request_id=topic_request_id,
    )

    async def _generate():
        """Async generation logic."""
        # Create fresh db_config for this async context
        from src.config.database import DatabaseConfig

        db_config = DatabaseConfig()
        try:
            async with db_config.session() as session:
                generator = await create_article_generator(session)
                article = await generator.generate_article(topic_request_id)
                return {
                    "article_id": article.id,
                    "title": article.title,
                    "word_count": article.word_count,
                    "status": "completed",
                }
        finally:
            await db_config.close()

    try:
        # Run async generation with new event loop
        result = asyncio.run(_generate())

        logger.info(
            "generate_article_task_completed",
            task_id=self.request.id,
            topic_request_id=topic_request_id,
            article_id=result["article_id"],
        )

        return result

    except Exception as e:
        logger.error(
            "generate_article_task_failed",
            task_id=self.request.id,
            topic_request_id=topic_request_id,
            error=str(e),
            exc_info=True,
        )
        raise
