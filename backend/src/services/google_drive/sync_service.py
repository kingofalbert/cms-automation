"""Google Drive synchronization service for worklist management."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

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

logger = get_logger(__name__)


class GoogleDriveSyncService:
    """Synchronize Google Drive documents into the worklist."""

    def __init__(self, session: AsyncSession, folder_id: Optional[str] = None) -> None:
        self.session = session
        self.settings = get_settings()
        self.folder_id = folder_id or self.settings.GOOGLE_DRIVE_FOLDER_ID
        self._storage = None

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
            "errors": [],
        }

        for file_metadata in files:
            summary["processed"] += 1
            try:
                parsed = await self._hydrate_document(storage, file_metadata)
                if parsed is None:
                    summary["skipped"] += 1
                    continue

                created = await self._upsert_worklist_item(parsed)
                if created:
                    summary["created"] += 1
                else:
                    summary["updated"] += 1
            except Exception as exc:
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

        return summary

    async def _get_storage(self):
        if self._storage is None:
            self._storage = await create_google_drive_storage()
        return self._storage

    async def _hydrate_document(self, storage, file_metadata: dict) -> Optional[dict[str, Any]]:
        """Retrieve and parse Drive document into worklist payload."""
        mime_type = file_metadata.get("mimeType")
        file_id = file_metadata.get("id")

        if not file_id:
            return None

        try:
            if mime_type == "application/vnd.google-apps.document":
                content = await self._export_google_doc(storage, file_id, "text/plain")
            elif mime_type and mime_type.startswith("text/"):
                raw = await storage.download_file(file_id)
                content = raw.decode("utf-8", errors="ignore")
            else:
                logger.info(
                    "google_drive_sync_skipped_file",
                    file_id=file_id,
                    mime_type=mime_type,
                )
                return None
        except Exception as exc:
            logger.error(
                "google_drive_fetch_failed",
                file_id=file_id,
                error=str(exc),
                exc_info=True,
            )
            raise

        parsed = self._parse_document_content(content)
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

    def _parse_document_content(self, content: str) -> dict[str, Any]:
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
        """
        # Try to parse YAML front matter
        yaml_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n(.*)$', re.DOTALL)
        yaml_match = yaml_pattern.match(content)

        if yaml_match and yaml is not None:
            front_matter_raw, body_content = yaml_match.groups()

            try:
                metadata = yaml.safe_load(front_matter_raw) or {}

                # Extract structured metadata
                title = metadata.get("title", "Untitled Document")
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

        # Fallback: Plain text parsing (no YAML front matter)
        lines = [line.strip() for line in content.splitlines()]
        lines = [line for line in lines if line]

        if not lines:
            title = "Untitled Document"
            body = ""
        else:
            title = lines[0][:500]
            body = "\n".join(lines[1:]) if len(lines) > 1 else ""

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

    async def _upsert_worklist_item(self, payload: dict[str, Any]) -> bool:
        """Insert or update worklist item and return True if created."""
        drive_metadata = payload.get("drive_metadata", {})
        drive_file_id = drive_metadata.get("id")

        if not drive_file_id:
            raise ValueError("Drive metadata missing file ID.")

        stmt = select(WorklistItem).where(WorklistItem.drive_file_id == drive_file_id)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        now = datetime.utcnow()
        metadata = dict(existing.metadata if existing else {})
        metadata.update(drive_metadata)

        if existing:
            existing.title = payload["title"]
            existing.content = payload["content"]
            existing.author = payload.get("author")
            existing.metadata = metadata
            existing.tags = payload.get("tags", [])
            existing.categories = payload.get("categories", [])
            existing.meta_description = payload.get("meta_description")
            existing.seo_keywords = payload.get("seo_keywords", [])
            existing.synced_at = now
            existing.updated_at = now
            self.session.add(existing)
            await self.session.commit()
            await self.session.refresh(existing)
            return False

        item = WorklistItem(
            drive_file_id=drive_file_id,
            title=payload["title"],
            status=WorklistStatus.TO_EVALUATE,
            content=payload["content"],
            author=payload.get("author"),
            tags=payload.get("tags", []),
            categories=payload.get("categories", []),
            meta_description=payload.get("meta_description"),
            seo_keywords=payload.get("seo_keywords", []),
            metadata=metadata,
            notes=payload.get("notes") or [],
            synced_at=now,
        )
        self.session.add(item)
        await self.session.commit()
        return True
