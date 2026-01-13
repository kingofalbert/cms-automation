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
from src.services.parser.html_utils import (
    strip_html_tags,
    calculate_plain_text_position,
    find_text_position_in_plain,
)
from src.services.worklist.diff_generator import generate_content_diff, generate_word_diff

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
                item.mark_status(WorklistStatus.FAILED)
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
                    # HOTFIX-PARSE-005: Use Google Drive title (article.title) as primary title_main
                    # The AI parser often confuses author line with title, so we prioritize
                    # the title from Google Drive file name which is more reliable
                    article.title_prefix = parsed_article.title_prefix
                    article.title_main = article.title or parsed_article.title_main
                    article.title_suffix = parsed_article.title_suffix
                    article.author_name = parsed_article.author_name
                    article.author_line = parsed_article.author_line
                    article.meta_description = parsed_article.meta_description
                    article.seo_keywords = parsed_article.seo_keywords or []
                    article.tags = parsed_article.tags or []
                    # Phase 10: WordPress taxonomy fields
                    article.primary_category = parsed_article.primary_category
                    article.focus_keyword = parsed_article.focus_keyword
                    # HOTFIX-PARSE-004: Save body_html to fix "0 字符" issue in UI
                    # HOTFIX-PARSE-006: Clean body_html by removing author line if present
                    clean_body_html = self._clean_body_html(
                        parsed_article.body_html,
                        parsed_article.author_line
                    )
                    article.body_html = clean_body_html
                    article.body = clean_body_html  # Sync for consistency
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
                        primary_category=parsed_article.primary_category,
                        focus_keyword=parsed_article.focus_keyword,
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
        """Persist proofreading output on the article record.

        Phase 8.4: Enhanced to save suggested_content and diff structure
        for the comparison view in ProofreadingReviewPanel.

        Spec 014: Enriches issues with plain text positions for accurate
        frontend highlighting of duplicate text occurrences.
        """
        # Convert issues to dicts and enrich with plain text positions
        html_content = article.body or ""
        issues_data = [issue.model_dump(mode="json") for issue in result.issues]

        # Spec 014: Enrich issues with plain_text_position for accurate frontend highlighting
        enriched_issues = self._enrich_issues_with_plain_text_positions(
            issues_data, html_content
        )

        article.proofreading_issues = enriched_issues
        article.critical_issues_count = result.statistics.blocking_issue_count

        # Phase 8.4: Save AI suggested content for diff view
        if result.suggested_content:
            article.suggested_content = result.suggested_content
            # Generate structured diff for frontend visualization
            article.suggested_content_changes = generate_content_diff(
                original=article.body or "",
                suggested=result.suggested_content
            )
            logger.info(
                "proofreading_suggested_content_saved",
                article_id=article.id,
                original_length=len(article.body or ""),
                suggested_length=len(result.suggested_content),
                has_changes=article.body != result.suggested_content,
            )

        # Save complete result to metadata (backup/audit)
        metadata = dict(article.article_metadata or {})
        metadata["proofreading"] = result.model_dump(mode="json")
        article.article_metadata = metadata

    def _enrich_issues_with_plain_text_positions(
        self,
        issues: list[dict[str, Any]],
        html_content: str,
    ) -> list[dict[str, Any]]:
        """Enrich proofreading issues with plain text positions.

        Spec 014: This method adds plain_text_position, original_text_plain,
        and suggested_text_plain to each issue for accurate frontend highlighting.

        The problem: AI returns positions based on HTML content, but the frontend
        displays plain text (without HTML tags). This causes position mismatches.

        Solution: Calculate plain text positions from HTML positions, and provide
        plain text versions of original/suggested text for fallback text search.

        Args:
            issues: List of issue dicts from ProofreadingResult
            html_content: The HTML content the issues reference

        Returns:
            List of enriched issue dicts with plain text position fields
        """
        if not html_content:
            return issues

        # Pre-compute plain text content for text search fallback
        plain_content = strip_html_tags(html_content)
        search_start_index = 0

        for issue in issues:
            try:
                # 1. Add plain text versions of text fields
                original_text = issue.get("original_text")
                if original_text:
                    issue["original_text_plain"] = strip_html_tags(original_text)

                # Use suggested_text (actual corrected text) for frontend Preview mode
                # Fall back to suggestion (description) if suggested_text not available
                suggested_text = issue.get("suggested_text")
                if suggested_text:
                    issue["suggested_text_plain"] = strip_html_tags(suggested_text)
                else:
                    # Legacy fallback: some rules may only have suggestion description
                    suggestion = issue.get("suggestion")
                    if suggestion:
                        issue["suggested_text_plain"] = strip_html_tags(suggestion)

                # 2. Calculate plain text position
                location = issue.get("location")
                if location and isinstance(location, dict):
                    html_start = location.get("start")
                    html_end = location.get("end")

                    if html_start is not None and html_end is not None:
                        try:
                            plain_pos = calculate_plain_text_position(
                                html_content, html_start, html_end
                            )
                            issue["plain_text_position"] = plain_pos.to_dict()
                            logger.debug(
                                "issue_plain_text_position_calculated",
                                html_pos=f"{html_start}-{html_end}",
                                plain_pos=f"{plain_pos.start}-{plain_pos.end}",
                            )
                        except ValueError as e:
                            logger.warning(
                                "issue_position_calculation_failed",
                                error=str(e),
                                location=location,
                            )

                # 3. Fallback: Use text search if position not set
                if "plain_text_position" not in issue:
                    search_text = issue.get("original_text_plain")
                    if search_text:
                        found_pos = find_text_position_in_plain(
                            plain_content, search_text, search_start_index
                        )
                        if found_pos:
                            issue["plain_text_position"] = found_pos.to_dict()
                            # Update search start for sequential issues
                            search_start_index = found_pos.end
                            logger.debug(
                                "issue_position_found_by_text_search",
                                text=search_text[:30],
                                position=found_pos.to_dict(),
                            )

            except Exception as e:
                logger.warning(
                    "issue_enrichment_failed",
                    issue_id=issue.get("rule_id"),
                    error=str(e),
                )
                continue

        return issues

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

    def _clean_body_html(
        self,
        body_html: str | None,
        author_line: str | None,
    ) -> str:
        """Clean body_html by removing author line, image metadata, and trailing keywords.

        HOTFIX-PARSE-006: Ensures body_html contains only the article content,
        without metadata that should be displayed separately.

        Args:
            body_html: Raw body HTML from parsing
            author_line: Extracted author line to remove

        Returns:
            Cleaned body HTML
        """
        import re
        from bs4 import BeautifulSoup

        if not body_html:
            return ""

        soup = BeautifulSoup(body_html, "html.parser")
        paragraphs = soup.find_all("p")

        # Track which paragraphs to remove
        paragraphs_to_remove = []

        for i, p in enumerate(paragraphs):
            text = p.get_text(strip=True)

            # Remove author line paragraph (usually first paragraph)
            if author_line and text and author_line.strip() in text:
                paragraphs_to_remove.append(p)
                logger.debug(f"Removing author line paragraph: {text[:50]}...")
                continue

            # Remove image metadata paragraphs (圖片, 圖片連結)
            if text and (
                text.startswith("圖片：") or
                text.startswith("圖片:") or
                text.startswith("圖片連結：") or
                text.startswith("圖片連結:") or
                text.startswith("圖說：") or
                text.startswith("圖說:")
            ):
                paragraphs_to_remove.append(p)
                logger.debug(f"Removing image metadata paragraph: {text[:50]}...")
                continue

            # Remove keyword/tag lines at the end (check last 5 paragraphs)
            if i >= len(paragraphs) - 5:
                # Detect keyword lines: comma/space separated short terms
                # Pattern: multiple short Chinese phrases separated by , or 、
                if text and len(text) < 300:
                    # Check if it looks like a keyword list
                    parts = re.split(r"[,，、\s]+", text)
                    if len(parts) >= 5:  # At least 5 keywords
                        # Check if all parts are short (keywords are usually < 15 chars)
                        if all(len(part.strip()) < 15 for part in parts if part.strip()):
                            paragraphs_to_remove.append(p)
                            logger.debug(f"Removing keyword paragraph: {text[:50]}...")
                            continue

        # Remove marked paragraphs
        for p in paragraphs_to_remove:
            p.decompose()

        # Return cleaned HTML
        result = str(soup)
        logger.info(
            "body_html_cleaned",
            original_length=len(body_html),
            cleaned_length=len(result),
            paragraphs_removed=len(paragraphs_to_remove),
        )
        return result
