"""Google Drive synchronization service for worklist management."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime
from html.parser import HTMLParser
from typing import Any

try:
    from googleapiclient.errors import HttpError
except ImportError:  # pragma: no cover - Google client optional in some environments
    HttpError = Exception  # type: ignore[assignment]
try:
    import yaml
except ImportError:  # pragma: no cover - PyYAML optional in some environments
    yaml = None  # type: ignore[assignment]
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.config.logging import get_logger
from src.models import WorklistItem, WorklistStatus
from src.services.storage import create_google_drive_storage
from src.services.worklist.pipeline import WorklistPipelineService

try:
    from src.services.google_drive.metrics import (
        DocumentMetrics,
        ExportStatus,
        ParsingStatus,
        get_metrics_collector,
    )
except ImportError:  # pragma: no cover - Metrics module optional for testing
    DocumentMetrics = None  # type: ignore[assignment,misc]
    ExportStatus = None  # type: ignore[assignment,misc]
    ParsingStatus = None  # type: ignore[assignment,misc]
    get_metrics_collector = lambda: None  # type: ignore[assignment]

logger = get_logger(__name__)


class GoogleDocsHTMLParser(HTMLParser):
    """Clean HTML parser for Google Docs exported content.

    Converts Google Docs HTML export to clean markdown-like text
    while preserving structure and basic formatting.
    """

    def __init__(self):
        super().__init__()
        self.content_parts = []
        self.current_list_level = 0
        self.in_paragraph = False
        self.current_text = []
        self.in_bold = False
        self.in_italic = False
        self.in_link = False
        self.link_url = None

    def handle_starttag(self, tag, attrs):
        """Handle opening HTML tags."""
        attrs_dict = dict(attrs)

        if tag in ('p', 'div'):
            self.in_paragraph = True
            self.current_text = []
        elif tag == 'br':
            self.current_text.append('\n')
        elif tag in ('b', 'strong'):
            self.in_bold = True
            # Add space before bold if needed
            if self.current_text and not self.current_text[-1].endswith((' ', '\n')):
                self.current_text.append(' ')
            self.current_text.append('**')
        elif tag in ('i', 'em'):
            self.in_italic = True
            # Add space before italic if needed
            if self.current_text and not self.current_text[-1].endswith((' ', '\n')):
                self.current_text.append(' ')
            self.current_text.append('_')
        elif tag == 'a':
            self.in_link = True
            self.link_url = attrs_dict.get('href', '')
            # Add space before link if needed
            if self.current_text and not self.current_text[-1].endswith((' ', '\n')):
                self.current_text.append(' ')
            self.current_text.append('[')
        elif tag in ('ul', 'ol'):
            self.current_list_level += 1
        elif tag == 'li':
            indent = '  ' * (self.current_list_level - 1)
            self.current_text.append(f'\n{indent}- ')
        elif tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            level = int(tag[1])
            self.current_text.append('\n' + '#' * level + ' ')
            self.in_paragraph = True

    def handle_endtag(self, tag):
        """Handle closing HTML tags."""
        if tag in ('p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            if self.current_text:
                text = ''.join(self.current_text).strip()
                if text:
                    self.content_parts.append(text)
                self.current_text = []
            self.in_paragraph = False
        elif tag in ('b', 'strong'):
            self.current_text.append('**')
            # Add space after bold marker
            self.current_text.append(' ')
            self.in_bold = False
        elif tag in ('i', 'em'):
            self.current_text.append('_')
            # Add space after italic marker
            self.current_text.append(' ')
            self.in_italic = False
        elif tag == 'a':
            if self.link_url:
                self.current_text.append(f']({self.link_url})')
            else:
                self.current_text.append(']')
            # Add space after link
            self.current_text.append(' ')
            self.in_link = False
            self.link_url = None
        elif tag in ('ul', 'ol'):
            self.current_list_level = max(0, self.current_list_level - 1)

    def handle_data(self, data):
        """Handle text content."""
        # Skip empty data
        if not data.strip():
            return

        self.current_text.append(data.strip())

    def get_clean_text(self) -> str:
        """Get the cleaned text content."""
        # Flush any remaining text
        if self.current_text:
            text = ''.join(self.current_text).strip()
            if text:
                self.content_parts.append(text)

        # Join parts with proper spacing
        result = '\n\n'.join(self.content_parts)

        # Clean up multiple newlines
        result = re.sub(r'\n{3,}', '\n\n', result)

        return result.strip()


class GoogleDriveSyncService:
    """Synchronize Google Drive documents into the worklist."""

    def __init__(self, session: AsyncSession, folder_id: str | None = None) -> None:
        self.session = session
        self.settings = get_settings()
        self.folder_id = folder_id or self.settings.GOOGLE_DRIVE_FOLDER_ID
        self._storage = None
        self.pipeline = WorklistPipelineService(session)
        self.metrics_collector = get_metrics_collector()

    async def sync_worklist(self, max_results: int = 100) -> dict[str, Any]:
        """Synchronize documents from Google Drive into worklist items."""
        storage = await self._get_storage()

        if not self.folder_id:
            raise ValueError("Google Drive folder ID is not configured.")

        try:
            files = await storage.list_files(folder_id=self.folder_id, max_results=max_results)
        except Exception as exc:
            logger.error("google_drive_sync_list_failed", error=str(exc), exc_info=True)
            raise

        summary = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "auto_processed": 0,
            "auto_failed": 0,
            "errors": [],
        }

        for file_metadata in files:
            summary["processed"] += 1
            try:
                parsed = await self._hydrate_document(storage, file_metadata)
                if parsed is None:
                    summary["skipped"] += 1
                    continue

                item, created = await self._upsert_worklist_item(parsed)
                if created:
                    summary["created"] += 1
                    try:
                        await self.pipeline.process_new_item(item)
                        summary["auto_processed"] += 1
                    except Exception as exc:
                        summary["auto_failed"] += 1
                        logger.error(
                            "worklist_pipeline_failed",
                            file_id=file_metadata.get("id"),
                            error=str(exc),
                            exc_info=True,
                        )
                else:
                    summary["updated"] += 1
                await self.session.commit()
            except Exception as exc:
                await self.session.rollback()
                logger.error(
                    "google_drive_sync_item_failed",
                    file_id=file_metadata.get("id"),
                    error=str(exc),
                    exc_info=True,
                )
                summary["errors"].append(
                    {
                        "file_id": file_metadata.get("id"),
                        "error": str(exc),
                    }
                )

        # Log metrics summary if available
        if self.metrics_collector:
            metrics_summary = self.metrics_collector.get_summary()
            logger.info("google_drive_sync_metrics", **metrics_summary)

        return summary

    async def _get_storage(self):
        if self._storage is None:
            self._storage = await create_google_drive_storage()
        return self._storage

    async def _hydrate_document(self, storage, file_metadata: dict) -> dict[str, Any] | None:
        """Retrieve and parse Drive document into worklist payload."""
        mime_type = file_metadata.get("mimeType")
        file_id = file_metadata.get("id")

        if not file_id:
            return None

        try:
            if mime_type == "application/vnd.google-apps.document":
                # Export as HTML to preserve formatting and structure
                import time
                start_time = time.time()

                html_content = await self._export_google_doc(storage, file_id, "text/html")

                # Record export success
                if self.metrics_collector and DocumentMetrics:
                    metrics = self.metrics_collector.record_export_success(
                        file_id=file_id,
                        file_name=file_metadata.get("name", "unknown"),
                        mime_type=mime_type,
                        original_size=len(html_content),
                    )

                # Parse and clean the HTML
                content, parsing_status = self._parse_html_content(html_content)

                parsing_time = (time.time() - start_time) * 1000  # Convert to ms

                # Update metrics with parsing results
                if self.metrics_collector and metrics:
                    metrics.parsing_status = parsing_status
                    metrics.cleaned_size_bytes = len(content)
                    metrics.parsing_time_ms = parsing_time
                    # Check for YAML front matter
                    metrics.has_yaml_front_matter = content.strip().startswith("---")
                    self.metrics_collector.record_document(metrics)

                logger.debug(
                    "google_doc_exported_and_parsed",
                    file_id=file_id,
                    original_size=len(html_content),
                    cleaned_size=len(content),
                    parsing_time_ms=parsing_time,
                    parsing_status=parsing_status.value if parsing_status else None,
                )
            elif mime_type and mime_type.startswith("text/"):
                raw = await storage.download_file(file_id)
                content = raw.decode("utf-8", errors="ignore")
            else:
                # Record skipped file
                if self.metrics_collector and ExportStatus:
                    self.metrics_collector.record_export_skipped(
                        file_id=file_id,
                        file_name=file_metadata.get("name", "unknown"),
                        mime_type=mime_type,
                        reason="Unsupported MIME type",
                    )

                logger.info(
                    "google_drive_sync_skipped_file",
                    file_id=file_id,
                    mime_type=mime_type,
                )
                return None
        except Exception as exc:
            # Record export failure
            if self.metrics_collector and ExportStatus:
                self.metrics_collector.record_export_failure(
                    file_id=file_id,
                    file_name=file_metadata.get("name", "unknown"),
                    mime_type=mime_type,
                    error=str(exc),
                )

            logger.error(
                "google_drive_fetch_failed",
                file_id=file_id,
                error=str(exc),
                exc_info=True,
            )
            raise

        # Parse content and use Drive file name as fallback title
        file_name = file_metadata.get("name")
        parsed = self._parse_document_content(content, file_name=file_name)

        # Store raw HTML for parser (Issue #2 fix)
        # Parser needs original HTML with <img> tags and structure
        if mime_type == "application/vnd.google-apps.document":
            parsed["raw_html"] = html_content

        parsed["drive_metadata"] = {
            "id": file_metadata.get("id"),
            "name": file_metadata.get("name"),
            "mimeType": mime_type,
            "webViewLink": file_metadata.get("webViewLink"),
            "createdTime": file_metadata.get("createdTime"),
        }
        return parsed

    async def _export_google_doc(self, storage, file_id: str, mime_type: str) -> str:
        """Export Google Doc to the requested MIME type."""
        try:
            request = storage.service.files().export(fileId=file_id, mimeType=mime_type)
            content = request.execute()
            if isinstance(content, bytes):
                return content.decode("utf-8", errors="ignore")
            return str(content)
        except HttpError as http_error:
            status = getattr(http_error, "resp", {}).status if hasattr(http_error, "resp") else None
            if status == 429:
                await asyncio.sleep(2)
                return await self._export_google_doc(storage, file_id, mime_type)
            raise

    def _parse_html_content(self, html_content: str) -> tuple[str, Any]:
        """Parse and clean HTML content from Google Docs export.

        Args:
            html_content: Raw HTML from Google Docs export

        Returns:
            Tuple of (cleaned text content, parsing status)
        """
        parser = GoogleDocsHTMLParser()
        try:
            parser.feed(html_content)
            cleaned_text = parser.get_clean_text()
            status = ParsingStatus.SUCCESS if ParsingStatus else None
            return cleaned_text, status
        except Exception as exc:
            # Fallback to plain HTML stripping if parsing fails
            logger.warning(
                "html_parsing_failed_using_fallback",
                error=str(exc),
            )
            # Simple HTML tag removal as fallback
            import html
            text = re.sub(r'<[^>]+>', '', html_content)
            text = html.unescape(text)
            status = ParsingStatus.FALLBACK if ParsingStatus else None
            return text.strip(), status

    def _parse_document_content(self, content: str, file_name: str | None = None) -> dict[str, Any]:
        """Parse raw document content into structured data.

        Supports YAML front matter format:
        ---
        title: Article Title
        meta_description: SEO description
        seo_keywords:
          - keyword1
          - keyword2
        tags:
          - Tag1
          - Tag2
        categories:
          - Category1
        author: Author Name
        ---
        Article body content here...

        Args:
            content: Raw document content
            file_name: Optional file name from Google Drive to use as fallback title
        """
        # Try to parse YAML front matter
        yaml_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n(.*)$', re.DOTALL)
        yaml_match = yaml_pattern.match(content)

        if yaml_match and yaml is not None:
            front_matter_raw, body_content = yaml_match.groups()

            try:
                metadata = yaml.safe_load(front_matter_raw) or {}

                # Extract structured metadata
                # Use file_name as fallback if title not in YAML
                title = metadata.get("title") or file_name or "Untitled Document"
                meta_description = metadata.get("meta_description")
                seo_keywords = metadata.get("seo_keywords", [])
                tags = metadata.get("tags", [])
                categories = metadata.get("categories", [])
                author = metadata.get("author")

                # Validate and normalize lists
                if not isinstance(seo_keywords, list):
                    seo_keywords = [seo_keywords] if seo_keywords else []
                if not isinstance(tags, list):
                    tags = [tags] if tags else []
                if not isinstance(categories, list):
                    categories = [categories] if categories else []

                logger.info(
                    "google_drive_yaml_parsed",
                    title=title,
                    has_meta_description=bool(meta_description),
                    seo_keywords_count=len(seo_keywords),
                    tags_count=len(tags),
                    categories_count=len(categories),
                )

                return {
                    "title": title[:500],  # Limit title length
                    "content": body_content.strip(),
                    "author": author,
                    "notes": [],
                    "meta_description": meta_description,
                    "seo_keywords": seo_keywords,
                    "tags": tags,
                    "categories": categories,
                }
            except yaml.YAMLError as exc:
                logger.warning(
                    "google_drive_yaml_parse_failed",
                    error=str(exc),
                    falling_back_to_plain_text=True,
                )
                # Fall back to plain text parsing

        # Fallback: Use file name as title if available, otherwise extract from content
        if file_name:
            # Use Google Drive file name as title (most reliable)
            title = file_name[:500]
            body = content.strip()
        else:
            # Extract from content as last resort
            lines = [line.strip() for line in content.splitlines()]
            lines = [line for line in lines if line]

            if not lines:
                title = "Untitled Document"
                body = ""
            else:
                # Try to find a reasonable title (skip CSS/style lines)
                title = "Untitled Document"
                title_line_idx = 0

                # Skip lines that look like CSS/style code
                for idx, line in enumerate(lines):
                    # Skip lines with CSS patterns
                    if line.startswith('.') or line.startswith('#') or '{' in line or '}' in line:
                        continue
                    # Found a potential title
                    if len(line) > 0:
                        title = line[:500]
                        title_line_idx = idx
                        break

                body = "\n".join(lines[title_line_idx + 1:]) if len(lines) > title_line_idx + 1 else ""

        return {
            "title": title,
            "content": body,
            "author": None,
            "notes": [],
            "meta_description": None,
            "seo_keywords": [],
            "tags": [],
            "categories": [],
        }

    async def _upsert_worklist_item(
        self, payload: dict[str, Any]
    ) -> tuple[WorklistItem, bool]:
        """Insert or update worklist item and return (item, created?)."""
        drive_metadata = payload.get("drive_metadata", {})
        drive_file_id = drive_metadata.get("id")

        if not drive_file_id:
            raise ValueError("Drive metadata missing file ID.")

        stmt = select(WorklistItem).where(WorklistItem.drive_file_id == drive_file_id)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        now = datetime.utcnow()
        metadata = dict(existing.drive_metadata if existing else {})
        metadata.update(drive_metadata)

        if existing:
            existing.title = payload["title"]
            existing.content = payload["content"]
            existing.raw_html = payload.get("raw_html")  # FIX: Save raw HTML for parser
            existing.drive_metadata = metadata
            existing.synced_at = now
            existing.updated_at = now

            # IMPORTANT: Only update these fields if they don't already have parsed values
            # This preserves data extracted by the AI parser (author, tags, meta_description, etc.)
            # The sync from Google Drive should NOT overwrite data that was parsed by AI
            if not existing.author:
                existing.author = payload.get("author")
            if not existing.tags:
                existing.tags = payload.get("tags", [])
            if not existing.categories:
                existing.categories = payload.get("categories", [])
            if not existing.meta_description:
                existing.meta_description = payload.get("meta_description")
            if not existing.seo_keywords:
                existing.seo_keywords = payload.get("seo_keywords", [])

            self.session.add(existing)
            await self.session.flush()
            return existing, False

        item = WorklistItem(
            drive_file_id=drive_file_id,
            title=payload["title"],
            status=WorklistStatus.PENDING,
            content=payload["content"],
            raw_html=payload.get("raw_html"),  # FIX: Save raw HTML for parser
            author=payload.get("author"),
            tags=payload.get("tags", []),
            categories=payload.get("categories", []),
            meta_description=payload.get("meta_description"),
            seo_keywords=payload.get("seo_keywords", []),
            drive_metadata=metadata,
            notes=payload.get("notes") or [],
            synced_at=now,
        )
        self.session.add(item)
        await self.session.flush()
        return item, True
