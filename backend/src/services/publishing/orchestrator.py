"""Publishing orchestrator coordinating provider execution and task tracking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.schemas.seo import SEOMetadata
from src.config import get_logger, get_settings
from src.config.database import get_db_config
from src.models import (
    Article,
    ArticleStatus,
    Provider,
    PublishTask,
    TaskStatus,
)
from src.services.computer_use_cms import create_computer_use_cms_service
from src.services.hybrid_publisher import create_hybrid_publisher
from src.services.providers.playwright_wordpress_publisher import (
    create_playwright_publisher,
)

logger = get_logger(__name__)


@dataclass(slots=True)
class PublishingContext:
    """Immutable snapshot of task + article data needed by providers."""

    publish_task_id: int
    article_id: int
    article_title: str
    article_body: str
    article_metadata: dict[str, Any]
    tags: list[str]
    categories: list[str]
    cms_url: str
    cms_type: str
    cms_username: str
    cms_password: str
    seo_metadata: SEOMetadata
    provider: Provider


class PublishingOrchestrator:
    """Coordinate publishing workflow across providers and persist progress."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._db_config = get_db_config()
        self._session_factory = self._db_config.get_session_factory()
        self.workflow_steps: list[TaskStatus] = [
            TaskStatus.INITIALIZING,
            TaskStatus.PUBLISHING,
        ]
        self.total_steps = len(self.workflow_steps) + 1  # include completion step

    async def publish_article(
        self,
        publish_task_id: int,
        article_id: int,
        provider: Provider | str,
        options: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Execute publishing workflow for the given task."""
        provider_enum = provider if isinstance(provider, Provider) else Provider(provider)
        options = options or {}

        context = await self._prepare_context(
            publish_task_id=publish_task_id,
            article_id=article_id,
            provider=provider_enum,
        )

        await self._update_progress(
            publish_task_id,
            TaskStatus.PUBLISHING,
            completed_steps=2,
        )

        try:
            result = await self._execute_provider(context, options)
        except Exception as exc:
            await self._handle_failure(publish_task_id, str(exc))
            logger.error(
                "publishing_workflow_failed",
                publish_task_id=publish_task_id,
                article_id=article_id,
                provider=provider_enum.value,
                error=str(exc),
                exc_info=True,
            )
            raise

        await self._finalize_success(publish_task_id, result)

        logger.info(
            "publishing_workflow_completed",
            publish_task_id=publish_task_id,
            article_id=article_id,
            provider=provider_enum.value,
        )

        return self._normalize_result(result, provider_enum)

    async def _prepare_context(
        self,
        publish_task_id: int,
        article_id: int,
        provider: Provider,
    ) -> PublishingContext:
        """Load task/article, mark as started, and capture execution context."""
        session: AsyncSession = self._session_factory()
        try:
            stmt = (
                select(PublishTask)
                .options(
                    selectinload(PublishTask.article).selectinload(Article.seo_metadata),
                )
                .where(PublishTask.id == publish_task_id)
            )
            result = await session.execute(stmt)
            task = result.scalar_one_or_none()

            if not task:
                raise ValueError(f"PublishTask {publish_task_id} not found")
            if task.article_id != article_id:
                raise ValueError(
                    f"PublishTask {publish_task_id} is not associated with article {article_id}"
                )
            if not task.article:
                raise ValueError(f"Article {article_id} not found for publish task")

            article = task.article
            task.provider = provider
            task.total_steps = self.total_steps
            task.screenshots = []
            task.error_message = None
            task.cms_type = task.cms_type or self.settings.CMS_TYPE
            task.cms_url = task.cms_url or self.settings.CMS_BASE_URL

            cms_username = self.settings.CMS_USERNAME
            cms_password = self.settings.CMS_APPLICATION_PASSWORD
            if not cms_username or not cms_password:
                raise RuntimeError("CMS credentials are not configured")

            task.mark_started()
            initial_progress = self._progress_for_step(1, task.total_steps)
            task.update_progress(TaskStatus.INITIALIZING.value, 1, initial_progress)

            if article.status != ArticleStatus.PUBLISHING:
                article.status = ArticleStatus.PUBLISHING
                article.published_at = None
                article.published_url = None

            session.add(task)
            session.add(article)
            await session.commit()

            return PublishingContext(
                publish_task_id=task.id,
                article_id=article.id,
                article_title=article.title or "",
                article_body=article.body or "",
                article_metadata=dict(article.article_metadata or {}),
                tags=article.tags or [],
                categories=article.categories or [],
                cms_url=task.cms_url,
                cms_type=task.cms_type,
                cms_username=cms_username,
                cms_password=cms_password,
                seo_metadata=self._build_seo_metadata(article),
                provider=provider,
            )
        finally:
            await session.close()

    async def _execute_provider(
        self,
        context: PublishingContext,
        options: dict[str, Any],
    ) -> dict[str, Any]:
        """Invoke provider-specific publishing implementation."""
        provider = context.provider

        if provider is Provider.PLAYWRIGHT:
            publisher = await create_playwright_publisher(
                options.get("playwright_config_path"),
            )
            result = await publisher.publish_article(
                cms_url=context.cms_url,
                username=context.cms_username,
                password=context.cms_password,
                article_title=context.article_title,
                article_body=context.article_body,
                seo_data=context.seo_metadata,
                article_images=options.get("article_images") or [],
                headless=options.get("headless", False),
            )
        elif provider is Provider.COMPUTER_USE:
            computer_use = await create_computer_use_cms_service()
            result = await computer_use.publish_article_with_seo(
                article_title=context.article_title,
                article_body=context.article_body,
                seo_data=context.seo_metadata,
                cms_url=context.cms_url,
                cms_username=context.cms_username,
                cms_password=context.cms_password,
                cms_type=context.cms_type,
                tags=context.tags,
                categories=context.categories,
                article_images=options.get("article_images") or [],
            )
        elif provider is Provider.HYBRID:
            hybrid = await create_hybrid_publisher(
                strategy=options.get("strategy", "auto"),
                playwright_config_path=options.get("playwright_config_path"),
            )
            result = await hybrid.publish_article(
                cms_url=context.cms_url,
                username=context.cms_username,
                password=context.cms_password,
                article_title=context.article_title,
                article_body=context.article_body,
                seo_data=context.seo_metadata,
                article_images=options.get("article_images") or [],
                article_metadata=context.article_metadata,
            )
        else:  # pragma: no cover - enum already exhaustive
            raise ValueError(f"Unsupported provider: {provider}")

        success = result.get("success")
        if success is not True:
            error_message = result.get("error") or "Publishing provider returned failure"
            raise RuntimeError(error_message)

        return result

    async def _finalize_success(
        self,
        publish_task_id: int,
        result: dict[str, Any],
    ) -> None:
        """Persist successful publishing outcome."""
        session: AsyncSession = self._session_factory()
        try:
            stmt = (
                select(PublishTask)
                .options(selectinload(PublishTask.article))
                .where(PublishTask.id == publish_task_id)
            )
            db_result = await session.execute(stmt)
            task = db_result.scalar_one_or_none()

            if not task:
                logger.warning(
                    "publish_task_missing_during_finalize",
                    publish_task_id=publish_task_id,
                )
                return

            article = task.article

            screenshots = self._collect_screenshots(result)
            if screenshots:
                task.screenshots = []
                for index, screenshot in enumerate(screenshots, start=1):
                    task.add_screenshot(
                        url=screenshot,
                        step=f"{TaskStatus.PUBLISHING.value}_{index}",
                    )

            task.mark_completed(cost_usd=self._extract_cost(result))
            task.error_message = None

            if article:
                article.cms_article_id = result.get("cms_article_id") or article.cms_article_id
                article.published_url = result.get("url") or article.published_url
                article.status = ArticleStatus.PUBLISHED
                article.published_at = article.published_at or datetime.utcnow()
                session.add(article)

            session.add(task)
            await session.commit()
        finally:
            await session.close()

    async def _handle_failure(self, publish_task_id: int, error: str) -> None:
        """Persist failure outcome for task and associated article."""
        session: AsyncSession = self._session_factory()
        try:
            stmt = (
                select(PublishTask)
                .options(selectinload(PublishTask.article))
                .where(PublishTask.id == publish_task_id)
            )
            result = await session.execute(stmt)
            task = result.scalar_one_or_none()
            if not task:
                logger.warning(
                    "publish_task_missing_during_failure",
                    publish_task_id=publish_task_id,
                )
                return

            truncated_error = (error or "Publishing task failed")[:500]
            task.mark_failed(truncated_error)

            if task.article:
                task.article.status = ArticleStatus.FAILED
                session.add(task.article)

            session.add(task)
            await session.commit()
        finally:
            await session.close()

    async def _update_progress(
        self,
        publish_task_id: int,
        status: TaskStatus,
        completed_steps: int,
    ) -> None:
        """Update task progress for the given workflow step."""
        session: AsyncSession = self._session_factory()
        try:
            task = await session.get(PublishTask, publish_task_id)
            if not task:
                return

            total_steps = task.total_steps or self.total_steps
            progress_value = self._progress_for_step(completed_steps, total_steps)

            task.update_progress(status.value, completed_steps, progress_value)
            session.add(task)
            await session.commit()
        finally:
            await session.close()

    def _progress_for_step(self, completed_steps: int, total_steps: int) -> int:
        """Calculate integer progress percentage for current step."""
        if total_steps <= 0:
            return 0
        progress = int((completed_steps / total_steps) * 100)
        return max(0, min(progress, 99))

    def _build_seo_metadata(self, article: Article) -> SEOMetadata:
        """Construct SEO metadata, falling back to sensible defaults on validation errors."""
        metadata: Dict[str, Any] = dict(article.article_metadata or {})
        seo_raw = metadata.get("seo") or {}

        try:
            return SEOMetadata(**seo_raw)
        except (ValidationError, TypeError):
            logger.warning(
                "seo_metadata_invalid_or_missing",
                article_id=article.id,
            )

        title = (article.title or "Published Article").strip()
        if len(title) < 50:
            title = (title + " ") * ((50 // max(len(title), 1)) + 1)
            title = title[:60]

        description_source = (article.body or title).strip()
        description = description_source[:160]
        while len(description) < 120:
            description += f" {title}"
            if len(description) >= 160:
                break
        description = description[:160]

        fallback = {
            "meta_title": title,
            "meta_description": description,
            "focus_keyword": title.split()[0] if title.split() else "article",
            "keywords": [title.split()[0]] if title.split() else ["article"],
            "canonical_url": None,
            "og_title": title[:70],
            "og_description": description[:200],
            "og_image": None,
            "schema_type": "Article",
            "readability_score": None,
            "seo_score": None,
        }

        return SEOMetadata(**fallback)

    def _collect_screenshots(self, result: dict[str, Any]) -> List[str]:
        """Extract screenshot URLs from provider result."""
        screenshots: List[str] = []

        primary = result.get("screenshots")
        if isinstance(primary, list):
            screenshots.extend(str(item) for item in primary if item)

        single = result.get("screenshot")
        if single:
            screenshots.append(str(single))

        metadata = result.get("metadata")
        if isinstance(metadata, dict):
            meta_shots = metadata.get("screenshots")
            if isinstance(meta_shots, list):
                screenshots.extend(str(item) for item in meta_shots if item)

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: List[str] = []
        for item in screenshots:
            if item not in seen:
                seen.add(item)
                unique.append(item)
        return unique

    def _extract_cost(self, result: dict[str, Any]) -> Optional[float]:
        """Extract cost (if provided) from provider result."""
        if "cost_usd" in result and isinstance(result["cost_usd"], (int, float)):
            return float(result["cost_usd"])
        metadata = result.get("metadata")
        cost_value = None
        if isinstance(metadata, dict):
            cost_value = metadata.get("cost_usd")
            if cost_value is None:
                usage = metadata.get("usage") or {}
                cost_value = usage.get("total_cost_usd")
        if isinstance(cost_value, (int, float)):
            return float(cost_value)
        return None

    def _normalize_result(
        self,
        result: dict[str, Any],
        provider: Provider,
    ) -> dict[str, Any]:
        """Ensure result payload is JSON-serializable and annotated with provider info."""
        normalized = dict(result)
        normalized["provider"] = provider.value
        return normalized
