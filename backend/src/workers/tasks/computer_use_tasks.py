"""Celery tasks for Computer Use CMS operations."""

import asyncio
from datetime import datetime
from typing import Any

from sqlalchemy import select

from src.api.schemas.seo import SEOMetadata
from src.config import get_logger, get_settings
from src.config.database import get_async_session
from src.models import Article, ArticleStatus
from src.services.drive_image_retriever import create_drive_image_retriever
from src.services.hybrid_publisher import create_hybrid_publisher
from src.workers.celery_app import celery_app

logger = get_logger(__name__)
settings = get_settings()


@celery_app.task(
    name="publish_article_with_computer_use",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def publish_article_with_computer_use_task(
    self,
    article_id: int,
    cms_url: str,
    cms_username: str,
    cms_password: str,
    cms_type: str = "wordpress",
    publishing_strategy: str = "auto",
) -> dict[str, Any]:
    """Publish article using Computer Use API (Celery task).

    Args:
        article_id: Article ID to publish
        cms_url: CMS admin URL
        cms_username: CMS username
        cms_password: CMS password or application password
        cms_type: CMS platform type

    Returns:
        dict: Publishing result
    """
    logger.info(
        "computer_use_publish_task_started",
        task_id=self.request.id,
        article_id=article_id,
        cms_type=cms_type,
    )

    try:
        # Run async operations in event loop
        result = asyncio.run(
            _publish_article_async(
                article_id=article_id,
                cms_url=cms_url,
                cms_username=cms_username,
                cms_password=cms_password,
                cms_type=cms_type,
                publishing_strategy=publishing_strategy,
            )
        )

        logger.info(
            "computer_use_publish_task_completed",
            task_id=self.request.id,
            article_id=article_id,
            success=result.get("success"),
        )

        return result

    except Exception as e:
        logger.error(
            "computer_use_publish_task_failed",
            task_id=self.request.id,
            article_id=article_id,
            error=str(e),
            exc_info=True,
        )

        # Retry on failure
        raise self.retry(exc=e) from e


async def _publish_article_async(
    article_id: int,
    cms_url: str,
    cms_username: str,
    cms_password: str,
    cms_type: str,
    publishing_strategy: str = "auto",
) -> dict[str, Any]:
    """Async helper for publishing article via Computer Use.

    Args:
        article_id: Article ID
        cms_url: CMS admin URL
        cms_username: Username
        cms_password: Password
        cms_type: CMS type

    Returns:
        dict: Publishing result
    """
    async with get_async_session() as session:
        # Get article from database
        result = await session.execute(select(Article).where(Article.id == article_id))
        article = result.scalar_one_or_none()

        if not article:
            raise ValueError(f"Article {article_id} not found")

        if article.status == ArticleStatus.PUBLISHED:
            logger.warning(
                "article_already_published",
                article_id=article_id,
            )
            return {
                "success": True,
                "message": "Article already published",
                "cms_article_id": article.cms_article_id,
            }

        # Extract SEO data from metadata
        seo_data_dict = article.article_metadata.get("seo", {})

        # Handle case where seo_data might be None or empty
        if not seo_data_dict:
            logger.warning(
                "article_missing_seo_data",
                article_id=article_id,
            )
            # Create default SEO data
            seo_data_dict = {
                "meta_title": article.title[:60],
                "meta_description": (article.body[:150] + "...")
                if len(article.body) > 150
                else article.body,
                "focus_keyword": article.title.split()[0] if article.title else "article",
                "keywords": [],
                "canonical_url": None,
                "og_title": article.title[:70],
                "og_description": (article.body[:200] + "...")
                if len(article.body) > 200
                else article.body,
                "og_image": None,
                "schema_type": "Article",
                "readability_score": None,
                "seo_score": None,
            }

        seo_data = SEOMetadata(**seo_data_dict)

        # Retrieve article images from Google Drive
        image_retriever = await create_drive_image_retriever(session)
        article_images = []

        try:
            article_images = await image_retriever.get_article_images(article_id)

            if article_images:
                logger.info(
                    "article_images_downloaded_from_drive",
                    article_id=article_id,
                    image_count=len(article_images),
                )

            # Initialize Hybrid Publisher
            # Check if Playwright config exists
            playwright_config_path = "/app/config/wordpress_selectors.json"
            import os
            if not os.path.exists(playwright_config_path):
                playwright_config_path = None
                logger.info("playwright_config_not_found_using_computer_use_only")

            hybrid_publisher = await create_hybrid_publisher(
                strategy=publishing_strategy,
                playwright_config_path=playwright_config_path,
            )

            publish_mode = "draft" if settings.ENVIRONMENT != "production" else "publish"

            # Publish article using hybrid strategy
            publish_result = await hybrid_publisher.publish_article(
                cms_url=cms_url,
                username=cms_username,
                password=cms_password,
                article_title=article.title,
                article_body=article.body,
                seo_data=seo_data,
                article_images=article_images,
                article_metadata=article.article_metadata or {},
                publish_mode=publish_mode,
            )

        finally:
            # Always cleanup temp files
            image_retriever.cleanup()
            logger.debug("cleaned_up_article_images", article_id=article_id)

        # Update article if publishing succeeded
        if publish_result.get("success"):
            article.cms_article_id = publish_result.get("cms_article_id")

            result_status = (publish_result.get("status") or "").lower()
            editor_url = publish_result.get("editor_url")
            public_url = publish_result.get("url")

            if result_status == "draft":
                article.status = ArticleStatus.DRAFT
                article.published_url = editor_url or public_url or article.published_url
                article.published_at = None
            else:
                article.status = ArticleStatus.PUBLISHED
                article.published_url = public_url or editor_url or article.published_url
                article.published_at = article.published_at or datetime.utcnow()

            # Update article metadata with Computer Use info
            article.article_metadata["computer_use"] = publish_result.get("metadata", {})

            await session.commit()

            logger.info(
                "article_published_via_computer_use",
                article_id=article_id,
                cms_article_id=article.cms_article_id,
                url=public_url,
                editor_url=editor_url,
                status=result_status or "unknown",
            )

        return publish_result


@celery_app.task(name="test_computer_use_environment")
def test_computer_use_environment_task() -> dict[str, Any]:
    """Test task to verify Computer Use environment is set up correctly.

    Returns:
        dict: Environment test results
    """
    import os
    import subprocess

    logger.info("testing_computer_use_environment")

    results = {
        "display": os.environ.get("DISPLAY"),
        "vnc_running": False,
        "browser_available": False,
        "anthropic_api_key_set": bool(os.environ.get("ANTHROPIC_API_KEY")),
    }

    # Check if VNC is running
    try:
        subprocess.run(["pgrep", "x11vnc"], check=True, capture_output=True)
        results["vnc_running"] = True
    except subprocess.CalledProcessError:
        results["vnc_running"] = False

    # Check if browser is available
    try:
        subprocess.run(
            ["which", "chromium"], check=True, capture_output=True, text=True
        )
        results["browser_available"] = True
    except subprocess.CalledProcessError:
        results["browser_available"] = False

    logger.info("computer_use_environment_test_completed", results=results)

    return results
