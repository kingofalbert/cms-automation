"""Celery task for article import."""

from typing import Any, Optional

from src.config.database import DatabaseConfig
from src.config.logging import get_logger
from src.services.article_importer import ArticleImportService
from src.workers.base_task import DatabaseTask
from src.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="import_articles",
    queue="article_import",
)
def import_articles_task(
    self,
    file_path: str,
    file_format: Optional[str] = None,
) -> dict[str, Any]:
    """Background task to import articles from a file.

    Args:
        file_path: Path to the import file
        file_format: File format (csv, json, wordpress). Auto-detected if None.

    Returns:
        dict: Import result with statistics
            {
                "task_id": str,
                "status": str,
                "total_records": int,
                "successful_imports": int,
                "failed_imports": int,
                "success_rate": float,
                "imported_article_ids": list[int],
                "errors": list[dict]
            }

    Raises:
        Exception: If import fails completely
    """
    import asyncio

    import nest_asyncio

    # Allow nested event loops (for Celery + asyncio)
    nest_asyncio.apply()

    logger.info(
        "import_articles_task_started",
        task_id=self.request.id,
        file_path=file_path,
        file_format=file_format,
    )

    async def _import() -> dict[str, Any]:
        """Async import logic."""
        # Create fresh db_config for this async context
        db_config = DatabaseConfig()
        try:
            async with db_config.session() as session:
                import_service = ArticleImportService(session)
                result = await import_service.import_from_file(
                    file_path=file_path,
                    file_format=file_format,
                )

                # Convert ImportResult to dict for JSON serialization
                return {
                    "task_id": self.request.id,
                    "status": "completed",
                    "total_records": result.total_records,
                    "successful_imports": result.successful_imports,
                    "failed_imports": result.failed_imports,
                    "success_rate": result.success_rate,
                    "imported_article_ids": result.imported_article_ids,
                    "errors": [
                        {
                            "row_number": error.row_number,
                            "error_message": error.error_message,
                            "raw_data": error.raw_data,
                        }
                        for error in result.errors
                    ],
                }
        finally:
            await db_config.close()

    try:
        # Run async import with new event loop
        result = asyncio.run(_import())

        logger.info(
            "import_articles_task_completed",
            task_id=self.request.id,
            file_path=file_path,
            total=result["total_records"],
            successful=result["successful_imports"],
            failed=result["failed_imports"],
            success_rate=f"{result['success_rate']:.1f}%",
        )

        return result

    except Exception as e:
        logger.error(
            "import_articles_task_failed",
            task_id=self.request.id,
            file_path=file_path,
            error=str(e),
            exc_info=True,
        )

        # Return error result
        return {
            "task_id": self.request.id,
            "status": "failed",
            "error": str(e),
            "total_records": 0,
            "successful_imports": 0,
            "failed_imports": 0,
            "success_rate": 0.0,
            "imported_article_ids": [],
            "errors": [],
        }
