"""Auto-publish service: Google Doc URL -> parse -> proofread -> WordPress draft.

Composes existing services (GoogleDriveSyncService, WorklistPipelineService,
PlaywrightWordPressPublisher) into a single automated pipeline callable by
Google Apps Script via the /v1/pipeline/auto-publish endpoint.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_logger, get_settings
from src.models import (
    Article,
    ArticleStatus,
    ArticleStatusHistory,
    ExecutionLog,
    ProofreadingDecision,
    ProofreadingHistory,
    PublishTask,
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

    async def cleanup_published_item(self, worklist_item_id: int) -> int:
        """Clean up large text fields from a published item to free Supabase storage.

        Nullifies large content columns and deletes associated history/log rows.
        Only operates on items with status 'published'.

        Returns estimated bytes freed.
        """
        item = await self.session.get(WorklistItem, worklist_item_id)
        if not item:
            raise ValueError(f"WorklistItem {worklist_item_id} not found")

        if item.status != WorklistStatus.PUBLISHED:
            raise ValueError(
                f"WorklistItem {worklist_item_id} status is '{item.status.value}', "
                f"expected 'published'"
            )

        freed_estimate = 0

        # --- Clean WorklistItem large fields ---
        if item.content:
            freed_estimate += len(item.content.encode("utf-8", errors="ignore"))
            item.content = ""  # nullable=False, use empty string
        if item.raw_html:
            freed_estimate += len(item.raw_html.encode("utf-8", errors="ignore"))
            item.raw_html = None
        if item.notes:
            freed_estimate += len(json.dumps(item.notes).encode("utf-8", errors="ignore"))
            item.notes = []
        self.session.add(item)

        # --- Clean Article large fields ---
        if item.article_id:
            article = await self.session.get(Article, item.article_id)
            if article:
                # body is nullable=False – replace with placeholder
                if article.body and len(article.body) > 100:
                    freed_estimate += len(article.body.encode("utf-8", errors="ignore"))
                    article.body = "[已清理 - 見 WordPress 草稿]"

                for field in (
                    "body_html",
                    "suggested_content",
                    "faq_html",
                    "faq_schema_proposals",
                    "paragraph_suggestions",
                    "paragraph_split_suggestions",
                    "suggested_content_changes",
                    "faq_assessment",
                    "faq_editorial_notes",
                ):
                    val = getattr(article, field, None)
                    if val is not None:
                        if isinstance(val, str):
                            freed_estimate += len(val.encode("utf-8", errors="ignore"))
                        else:
                            freed_estimate += len(json.dumps(val).encode("utf-8", errors="ignore"))
                        setattr(article, field, None)

                # JSONB fields that should be reset to empty list
                if article.proofreading_issues:
                    freed_estimate += len(
                        json.dumps(article.proofreading_issues).encode("utf-8", errors="ignore")
                    )
                    article.proofreading_issues = []

                self.session.add(article)

                # --- Delete associated history/log rows ---
                article_id = article.id

                # article_status_history
                result = await self.session.execute(
                    delete(ArticleStatusHistory).where(
                        ArticleStatusHistory.article_id == article_id
                    )
                )
                freed_estimate += (result.rowcount or 0) * 200  # ~200 bytes/row

                # proofreading_decisions
                result = await self.session.execute(
                    delete(ProofreadingDecision).where(
                        ProofreadingDecision.article_id == article_id
                    )
                )
                freed_estimate += (result.rowcount or 0) * 500  # ~500 bytes/row

                # proofreading_history
                result = await self.session.execute(
                    delete(ProofreadingHistory).where(
                        ProofreadingHistory.article_id == article_id
                    )
                )
                freed_estimate += (result.rowcount or 0) * 1000  # ~1KB/row

                # execution_logs (via publish_tasks)
                task_ids_result = await self.session.execute(
                    select(PublishTask.id).where(
                        PublishTask.article_id == article_id
                    )
                )
                task_ids = [row[0] for row in task_ids_result.all()]

                if task_ids:
                    result = await self.session.execute(
                        delete(ExecutionLog).where(
                            ExecutionLog.task_id.in_(task_ids)
                        )
                    )
                    freed_estimate += (result.rowcount or 0) * 300  # ~300 bytes/row

                    # publish_tasks
                    result = await self.session.execute(
                        delete(PublishTask).where(
                            PublishTask.article_id == article_id
                        )
                    )
                    freed_estimate += (result.rowcount or 0) * 500  # ~500 bytes/row

        await self.session.commit()

        logger.info(
            "cleanup_completed",
            worklist_item_id=worklist_item_id,
            article_id=item.article_id,
            freed_bytes_estimate=freed_estimate,
        )

        return freed_estimate

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

        # Download featured image if it's a URL (Playwright needs local file path)
        local_featured_image = None
        if featured_image_path and featured_image_path.startswith("http"):
            try:
                local_featured_image = await self._download_image_to_temp(featured_image_path)
                featured_image_path = local_featured_image
            except Exception as img_err:
                logger.warning(
                    "featured_image_download_failed",
                    url=featured_image_path[:100],
                    error=str(img_err),
                )
                featured_image_path = None  # Skip featured image if download fails

        try:
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
        finally:
            # Clean up temp file
            if local_featured_image:
                try:
                    os.unlink(local_featured_image)
                except OSError:
                    pass

    async def _download_image_to_temp(self, url: str) -> str:
        """Download image from URL to a temporary file. Returns local path."""
        import httpx

        # Handle Google Drive URLs: extract file ID and use Drive API
        drive_match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
        if drive_match:
            file_id = drive_match.group(1)
            storage = await create_google_drive_storage()
            data = storage.service.files().get_media(fileId=file_id).execute()
        else:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, follow_redirects=True)
                resp.raise_for_status()
                data = resp.content

        suffix = ".jpg"  # Default
        for ext in (".png", ".webp", ".gif", ".jpeg"):
            if ext in url.lower():
                suffix = ext
                break

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(data)
        tmp.close()
        return tmp.name
