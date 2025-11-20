"""Workflow helpers that connect Worklist items to Article + Proofreading pipelines."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_logger, get_settings
from src.models import (
    Article,
    ArticleStatus,
    ArticleStatusHistory,
    WorklistItem,
    WorklistStatus,
)
from src.services.proofreading import (
    ArticlePayload,
    ArticleSection,
    ProofreadingAnalysisService,
    ProofreadingResult,
)
from src.services.parser import ArticleParserService

logger = get_logger(__name__)


class WorklistPipelineService:
    """Create articles from Worklist items and trigger automatic proofreading."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        proofreading_service: ProofreadingAnalysisService | None = None,
        parser_service: ArticleParserService | None = None,
    ) -> None:
        self.session = session
        self.settings = get_settings()
        self.proofreading_service = proofreading_service or ProofreadingAnalysisService()

        # Phase 7.5: Support unified parsing (parsing + SEO + proofreading + FAQ)
        use_unified = getattr(self.settings, 'USE_UNIFIED_PARSER', False)
        self.parser_service = parser_service or ArticleParserService(
            use_ai=True,
            anthropic_api_key=self.settings.ANTHROPIC_API_KEY,
            use_unified_prompt=use_unified,
        )

    async def process_new_item(self, item: WorklistItem) -> None:
        """Ensure article exists for the worklist item, run parsing, then proofreading."""
        article = await self._ensure_article(item)

        # Step 1: Parse document to extract author, images, SEO, etc.
        parsing_success = await self._run_parsing(item)

        # Step 2: Only run proofreading if parsing succeeded
        if parsing_success:
            await self._run_proofreading(item, article)
        else:
            logger.info(
                "worklist_skipped_proofreading",
                worklist_id=item.id,
                reason="parsing_failed_or_needs_review",
                status=item.status.value if item.status else None,
            )

    async def _ensure_article(self, item: WorklistItem) -> Article:
        """Create an article for the worklist item if needed."""
        if item.article_id:
            article = await self.session.get(Article, item.article_id)
            if article:
                return article

        metadata = dict(item.drive_metadata or {})
        metadata.setdefault("worklist_id", item.id)
        metadata.setdefault("google_drive", {})
        metadata["google_drive"]["file_id"] = item.drive_file_id

        article = Article(
            title=item.title,
            body=item.content,
            status=ArticleStatus.IMPORTED,
            author_id=self.settings.GOOGLE_DRIVE_DEFAULT_AUTHOR_ID,
            source="google_drive",
            article_metadata=metadata,
            formatting={},
        )
        self.session.add(article)
        await self.session.flush()

        item.article_id = article.id
        item.mark_status(WorklistStatus.PENDING)
        self.session.add(item)

        await self._record_status_history(
            article=article,
            old_status=None,
            new_status=ArticleStatus.IMPORTED,
            reason="google_drive_imported",
            metadata={"worklist_id": item.id},
        )
        return article

    async def _run_parsing(self, item: WorklistItem) -> bool:
        """Parse document content to extract structured data (author, images, SEO, etc.).

        Returns:
            True if parsing succeeded and item is ready for next stage
            False if parsing failed or needs manual review
        """
        try:
            # Get the raw HTML content from the worklist item (Issue #2 fix)
            # Use raw_html if available (contains <img> tags and structure),
            # fallback to cleaned content for backward compatibility
            raw_html = item.raw_html or item.content

            if not item.raw_html:
                logger.warning(
                    "worklist_parsing_no_raw_html",
                    worklist_id=item.id,
                    message="Using cleaned text as fallback (raw HTML not available)",
                )

            # Call ArticleParserService to parse the document
            logger.info(
                "worklist_parsing_started",
                worklist_id=item.id,
                content_length=len(raw_html),
                has_raw_html=bool(item.raw_html),
            )

            # Parse with AI (will fallback to heuristics if AI fails)
            parsing_result = self.parser_service.parse_document(raw_html)

            if not parsing_result.success:
                # Parsing failed
                error_messages = [e.error_message for e in parsing_result.errors]
                logger.error(
                    "worklist_parsing_failed",
                    worklist_id=item.id,
                    errors=error_messages,
                )
                item.mark_status(WorklistStatus.PARSING)  # Stay in parsing status
                item.add_note(
                    {
                        "message": "AI解析失败，需要手动审核",
                        "level": "error",
                        "details": "; ".join(error_messages),
                    }
                )
                self.session.add(item)
                return False  # Signal failure to caller

            # Parsing succeeded - extract data from ParsedArticle
            parsed_article = parsing_result.parsed_article

            # HOTFIX-PARSE-003: Update Article table with parsed data
            if item.article_id:
                article = await self.session.get(Article, item.article_id)
                if article:
                    # Update article parsing fields
                    article.title_prefix = parsed_article.title_prefix
                    article.title_main = parsed_article.title_main
                    article.title_suffix = parsed_article.title_suffix
                    article.author_name = parsed_article.author_name
                    article.author_line = parsed_article.author_line
                    article.meta_description = parsed_article.meta_description
                    article.seo_keywords = parsed_article.seo_keywords or []
                    article.tags = parsed_article.tags or []
                    article.parsing_confirmed = False  # Needs manual review

                    # Phase 7.5: Update unified AI parsing fields
                    article.suggested_meta_description = parsed_article.suggested_meta_description
                    article.suggested_seo_keywords = parsed_article.suggested_seo_keywords or []
                    article.suggested_titles = parsed_article.suggested_titles
                    article.proofreading_issues = parsed_article.proofreading_issues or []
                    article.proofreading_stats = parsed_article.proofreading_stats
                    # Note: article.faqs is a relationship, not a column - skip assignment to avoid async error

                    # Update article metadata with parsing info
                    article_metadata = dict(article.article_metadata or {})
                    article_metadata["parsing"] = {
                        "method": parsed_article.parsing_method,
                        "confidence": parsed_article.parsing_confidence,
                        "parsed_at": datetime.utcnow().isoformat(),
                    }
                    article.article_metadata = article_metadata

                    self.session.add(article)

                    logger.info(
                        "article_parsing_fields_updated",
                        article_id=article.id,
                        worklist_id=item.id,
                        title_main=parsed_article.title_main,
                        author_name=parsed_article.author_name,
                    )

            # Update worklist item with parsed data
            item.author = parsed_article.author_name
            item.meta_description = parsed_article.meta_description
            item.seo_keywords = parsed_article.seo_keywords or []
            item.tags = parsed_article.tags or []

            # Store parsed images and other metadata in drive_metadata
            metadata = dict(item.drive_metadata or {})

            if parsed_article.images:
                metadata["images"] = [
                    {
                        "position": img.position,
                        "source_url": img.source_url,
                        "caption": img.caption,
                    }
                    for img in parsed_article.images
                ]
                # Set featured image from first image if available
                if parsed_article.images:
                    metadata["featured_image_path"] = parsed_article.images[0].source_url

            # Store title components
            metadata["title_prefix"] = parsed_article.title_prefix
            metadata["title_main"] = parsed_article.title_main
            metadata["title_suffix"] = parsed_article.title_suffix
            metadata["author_line"] = parsed_article.author_line

            # Store parsing metadata
            metadata["parsing"] = {
                "method": parsed_article.parsing_method,
                "confidence": parsed_article.parsing_confidence,
                "parsed_at": datetime.utcnow().isoformat(),
            }

            item.drive_metadata = metadata

            # Update status to PARSING_REVIEW
            item.mark_status(WorklistStatus.PARSING_REVIEW)
            item.add_note(
                {
                    "message": "AI解析完成，等待人工审核解析结果",
                    "level": "info",
                    "metadata": {
                        "author": parsed_article.author_name,
                        "images_count": len(parsed_article.images) if parsed_article.images else 0,
                        "parsing_method": parsed_article.parsing_method,
                    },
                }
            )

            self.session.add(item)

            logger.info(
                "worklist_parsing_completed",
                worklist_id=item.id,
                author=parsed_article.author_name,
                images_count=len(parsed_article.images) if parsed_article.images else 0,
                parsing_method=parsed_article.parsing_method,
            )

            return True  # Signal success to caller

        except Exception as exc:
            logger.error(
                "worklist_parsing_exception",
                worklist_id=item.id,
                error=str(exc),
                exc_info=True,
            )
            item.mark_status(WorklistStatus.PARSING)
            item.add_note(
                {
                    "message": "解析过程异常，需要重试",
                    "level": "error",
                    "details": str(exc),
                }
            )
            self.session.add(item)
            return False  # Signal failure to caller

    async def _run_proofreading(self, item: WorklistItem, article: Article) -> None:
        """Invoke AI + deterministic proofreading and persist the results."""
        payload = self._build_payload(article, item)

        try:
            result = await self.proofreading_service.analyze_article(payload)
        except Exception as exc:
            logger.error(
                "worklist_auto_proofreading_failed",
                worklist_id=item.id,
                article_id=article.id,
                error=str(exc),
                exc_info=True,
            )
            item.mark_status(WorklistStatus.FAILED)
            item.add_note(
                {
                    "message": "自动校对失败，等待人工重试",
                    "level": "error",
                    "details": str(exc),
                }
            )
            await self._record_status_history(
                article=article,
                old_status=article.status,
                new_status=ArticleStatus.FAILED,
                reason="auto_proofreading_failed",
                metadata={"error": str(exc)},
            )
            article.status = ArticleStatus.FAILED
            self.session.add_all([article, item])
            return

        self._apply_proofreading_result(article, result)

        item.mark_status(WorklistStatus.PROOFREADING_REVIEW)
        item.add_note(
            {
                "message": "自动校对完成，等待人工审核校对问题",
                "level": "info",
                "metadata": {
                    "issue_count": len(result.issues),
                    "blocking_issues": result.statistics.blocking_issue_count,
                },
            }
        )
        await self._record_status_history(
            article=article,
            old_status=article.status,
            new_status=ArticleStatus.IN_REVIEW,
            reason="auto_proofreading_completed",
            metadata={
                "issues": len(result.issues),
                "blocking": result.statistics.blocking_issue_count,
            },
        )
        article.status = ArticleStatus.IN_REVIEW
        self.session.add_all([article, item])

    def _build_payload(self, article: Article, item: WorklistItem) -> ArticlePayload:
        """Construct the payload sent to the proofreading orchestrator."""
        sections = [
            ArticleSection(kind="body", content=article.body),
        ]

        metadata = dict(article.article_metadata or {})
        metadata.setdefault("worklist_id", item.id)
        metadata.setdefault("drive_metadata", item.drive_metadata or {})

        return ArticlePayload(
            article_id=article.id,
            title=article.title,
            original_content=article.body,
            html_content=metadata.get("html"),
            sections=sections,
            metadata=metadata,
            keywords=item.seo_keywords or [],
            meta_description=item.meta_description,
            seo_keywords=item.seo_keywords or [],
            tags=item.tags or [],
            categories=item.categories or [],
            target_locale=metadata.get("target_locale") or "zh-TW",
        )

    def _apply_proofreading_result(
        self,
        article: Article,
        result: ProofreadingResult,
    ) -> None:
        """Persist proofreading output on the article record."""
        article.proofreading_issues = [
            issue.model_dump(mode="json") for issue in result.issues
        ]
        article.critical_issues_count = result.statistics.blocking_issue_count

        metadata = dict(article.article_metadata or {})
        metadata["proofreading"] = result.model_dump(mode="json")
        article.article_metadata = metadata

    async def _record_status_history(
        self,
        *,
        article: Article,
        old_status: ArticleStatus | str | None,
        new_status: ArticleStatus,
        reason: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Append a row to article_status_history."""
        history = ArticleStatusHistory(
            article_id=article.id,
            old_status=self._status_to_str(old_status),
            new_status=self._status_to_str(new_status),
            changed_by="system",
            change_reason=reason,
            metadata=metadata or {},
            created_at=datetime.utcnow(),
        )
        self.session.add(history)

    @staticmethod
    def _status_to_str(status: ArticleStatus | str | None) -> str | None:
        if status is None:
            return None
        if isinstance(status, ArticleStatus):
            return status.value
        return status
