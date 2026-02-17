"""Auto-publish service: Google Doc URL -> parse -> proofread -> WordPress draft.

Composes existing services (GoogleDriveSyncService, WorklistPipelineService,
PlaywrightWordPressPublisher) into a single automated pipeline callable by
Google Apps Script via the /v1/pipeline/auto-publish endpoint.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_logger, get_settings
from src.models import (
    Article,
    ArticleStatus,
    WorklistItem,
    WorklistStatus,
)
from src.services.google_drive.sync_service import GoogleDriveSyncService
from src.services.storage import create_google_drive_storage
from src.services.worklist.pipeline import WorklistPipelineService

logger = get_logger(__name__)

# Regex to extract file ID from various Google Docs URL formats
_GDOC_FILE_ID_RE = re.compile(r"/document/d/([a-zA-Z0-9_-]+)")


class AutoPublishService:
    """Orchestrate the full auto-publish pipeline for a single Google Doc."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def process_google_doc(
        self,
        google_doc_url: str,
        sheet_row: int | None = None,
        requester: str = "gas-automation",
    ) -> dict[str, Any]:
        """Run the full pipeline: fetch doc -> parse -> proofread -> publish draft.

        Returns a dict with worklist_item_id, article_id, wordpress_draft_url,
        wordpress_post_id, and status.
        """
        # 1. Extract file_id from the URL
        file_id = self._extract_file_id(google_doc_url)
        if not file_id:
            raise ValueError(
                f"Could not extract Google Doc file ID from URL: {google_doc_url}"
            )

        logger.info(
            "auto_publish_started",
            file_id=file_id,
            google_doc_url=google_doc_url,
            sheet_row=sheet_row,
            requester=requester,
        )

        # 2. Idempotency: check for an existing WorklistItem with same drive_file_id
        existing = await self._find_existing_item(file_id)
        if existing and existing.wordpress_draft_url:
            logger.info(
                "auto_publish_already_published",
                worklist_item_id=existing.id,
                wordpress_draft_url=existing.wordpress_draft_url,
            )
            return {
                "worklist_item_id": existing.id,
                "article_id": existing.article_id,
                "wordpress_draft_url": existing.wordpress_draft_url,
                "wordpress_post_id": existing.wordpress_post_id,
                "status": "already_published",
            }

        # 3. Fetch the Google Doc via Drive API
        storage = await create_google_drive_storage()

        file_metadata = (
            storage.service.files()
            .get(fileId=file_id, fields="id,name,mimeType,webViewLink,createdTime")
            .execute()
        )

        # 4. Hydrate the document (download + parse HTML)
        sync_service = GoogleDriveSyncService(self.session)
        parsed = await sync_service._hydrate_document(storage, file_metadata)
        if parsed is None:
            raise ValueError(
                f"Unsupported document format for file {file_id} "
                f"(mimeType: {file_metadata.get('mimeType')})"
            )

        # 5. Upsert worklist item
        item, created = await sync_service._upsert_worklist_item(parsed)
        await self.session.commit()

        logger.info(
            "auto_publish_worklist_item_ready",
            worklist_item_id=item.id,
            created=created,
        )

        # 6. Run parse + proofread pipeline
        pipeline = WorklistPipelineService(self.session)
        await pipeline.process_new_item(item)
        await self.session.commit()

        # 7. Auto-advance past review gates -> READY_TO_PUBLISH
        item.mark_status(WorklistStatus.READY_TO_PUBLISH)
        item.add_note({
            "message": "自動跳過審核（GAS 自動發佈流程）",
            "level": "info",
            "metadata": {"requester": requester, "sheet_row": sheet_row},
        })
        if item.article_id:
            article = await self.session.get(Article, item.article_id)
            if article:
                article.status = ArticleStatus.READY_TO_PUBLISH
                self.session.add(article)
        self.session.add(item)
        await self.session.commit()

        # 8. Publish as WordPress draft
        result = await self._publish_as_draft(item)
        await self.session.commit()

        return result

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_file_id(url: str) -> str | None:
        """Extract Google Drive file ID from a Google Docs URL."""
        match = _GDOC_FILE_ID_RE.search(url)
        return match.group(1) if match else None

    async def _find_existing_item(self, drive_file_id: str) -> WorklistItem | None:
        stmt = select(WorklistItem).where(
            WorklistItem.drive_file_id == drive_file_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _publish_as_draft(self, item: WorklistItem) -> dict[str, Any]:
        """Publish a worklist item as a WordPress draft using Playwright."""
        from src.api.schemas.seo import SEOMetadata
        from src.services.providers.playwright_wordpress_publisher import (
            PlaywrightWordPressPublisher,
        )

        settings = self.settings

        if not settings.CMS_BASE_URL:
            raise RuntimeError("CMS_BASE_URL is not configured")

        # Prepare article data
        article = None
        if item.article_id:
            article = await self.session.get(Article, item.article_id)

        title = item.title or "Untitled"
        body = item.content or ""

        # Build extended publishing data from article
        primary_category = None
        secondary_categories: list[str] = []
        tags: list[str] = []
        featured_image_path = None
        article_images: list[dict[str, Any]] = []
        seo_data = None

        if article:
            primary_category = getattr(article, "primary_category", None)
            secondary_categories = getattr(article, "secondary_categories", None) or []
            tags = getattr(article, "tags", None) or []
            featured_image_path = getattr(article, "featured_image_path", None)

            # Build SEO metadata
            seo_title = getattr(article, "seo_title", None) or title
            meta_desc = (
                getattr(article, "meta_description", None)
                or getattr(article, "suggested_meta_description", None)
                or ""
            )
            focus_kw = getattr(article, "focus_keyword", None) or ""
            seo_kws = getattr(article, "seo_keywords", None) or []

            if seo_title or meta_desc or focus_kw:
                seo_data = SEOMetadata(
                    meta_title=seo_title[:60] if seo_title else title[:60],
                    meta_description=meta_desc[:160] if meta_desc else "",
                    focus_keyword=focus_kw,
                    keywords=seo_kws[:5] if seo_kws else [],
                )

            # Use body_html from article if available (cleaner content)
            if getattr(article, "body_html", None):
                body = article.body_html
            elif getattr(article, "body", None):
                body = article.body

        # HTTP auth
        http_auth = None
        if settings.CMS_HTTP_AUTH_USERNAME and settings.CMS_HTTP_AUTH_PASSWORD:
            http_auth = (settings.CMS_HTTP_AUTH_USERNAME, settings.CMS_HTTP_AUTH_PASSWORD)

        publisher = PlaywrightWordPressPublisher()

        try:
            result = await publisher.publish_article(
                cms_url=settings.CMS_BASE_URL,
                username=settings.CMS_USERNAME,
                password=settings.CMS_APPLICATION_PASSWORD,
                article_title=title,
                article_body=body,
                seo_data=seo_data,
                article_images=article_images,
                headless=True,
                publish_mode="draft",
                http_auth=http_auth,
                primary_category=primary_category,
                secondary_categories=secondary_categories,
                tags=tags,
                featured_image_path=featured_image_path,
            )
        except Exception as exc:
            logger.error(
                "auto_publish_playwright_failed",
                worklist_item_id=item.id,
                error=str(exc),
                exc_info=True,
            )
            item.mark_status(WorklistStatus.FAILED)
            item.add_note({
                "message": f"WordPress 發佈失敗: {exc}",
                "level": "error",
            })
            self.session.add(item)
            return {
                "worklist_item_id": item.id,
                "article_id": item.article_id,
                "wordpress_draft_url": None,
                "wordpress_post_id": None,
                "status": "failed",
                "error": str(exc),
            }

        # Process result
        if result.get("success"):
            wordpress_draft_url = result.get("editor_url") or result.get("url")
            wordpress_post_id = result.get("cms_article_id")

            item.wordpress_draft_url = wordpress_draft_url
            item.wordpress_post_id = (
                int(wordpress_post_id) if wordpress_post_id else None
            )
            item.wordpress_draft_uploaded_at = datetime.utcnow()
            item.mark_status(WorklistStatus.PUBLISHED)
            item.add_note({
                "message": "已自動發佈為 WordPress 草稿",
                "level": "info",
                "metadata": {
                    "wordpress_post_id": wordpress_post_id,
                    "wordpress_draft_url": wordpress_draft_url,
                },
            })

            if article:
                article.status = ArticleStatus.DRAFT
                article.published_url = wordpress_draft_url
                article.cms_article_id = str(wordpress_post_id) if wordpress_post_id else None
                self.session.add(article)

            self.session.add(item)

            logger.info(
                "auto_publish_completed",
                worklist_item_id=item.id,
                wordpress_post_id=wordpress_post_id,
                wordpress_draft_url=wordpress_draft_url,
            )

            return {
                "worklist_item_id": item.id,
                "article_id": item.article_id,
                "wordpress_draft_url": wordpress_draft_url,
                "wordpress_post_id": wordpress_post_id,
                "status": "completed",
            }
        else:
            error_msg = result.get("error", "Unknown publishing error")
            item.mark_status(WorklistStatus.FAILED)
            item.add_note({
                "message": f"WordPress 發佈失敗: {error_msg}",
                "level": "error",
            })
            self.session.add(item)

            return {
                "worklist_item_id": item.id,
                "article_id": item.article_id,
                "wordpress_draft_url": None,
                "wordpress_post_id": None,
                "status": "failed",
                "error": error_msg,
            }
