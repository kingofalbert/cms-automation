"""JSON article importer."""

import json
from pathlib import Path
from typing import Any, Optional

from src.config import get_logger
from src.models import ArticleStatus
from src.services.article_importer.base import ArticleImporter, ImportedArticle

logger = get_logger(__name__)


class JSONImporter(ArticleImporter):
    """Import articles from JSON files.

    Expected JSON format:
    {
        "articles": [
            {
                "title": "Article Title",
                "body": "Article content...",
                "author_id": "123",
                "status": "imported",
                "featured_image_path": "/images/cover.jpg",
                "published_at": "2025-01-01 10:00:00",
                "seo": {
                    "meta_title": "SEO Title (50-60 chars)",
                    "meta_description": "SEO Description (150-160 chars)",
                    "focus_keyword": "keyword",
                    "primary_keywords": ["keyword1", "keyword2", "keyword3"],
                    "secondary_keywords": ["key1", "key2", "key3", "key4", "key5"],
                    "readability_score": 72.5,
                    "seo_score": 88.3
                }
            }
        ]
    }

    Required fields:
        - title: Article title
        - body: Article content
        - author_id: Author identifier

    Optional fields:
        - status: Article status (defaults to IMPORTED)
        - featured_image_path: Path to featured image
        - additional_images: Array of image paths
        - cms_article_id: CMS platform article ID
        - published_url: Public URL
        - published_at: Publication timestamp
        - article_metadata: Object with metadata
        - formatting: Object with formatting preferences
        - seo: SEO metadata object (optional)
    """

    def __init__(self) -> None:
        """Initialize JSON importer."""
        super().__init__(source_type="json_import")

    async def parse_file(self, file_path: str) -> list[ImportedArticle]:
        """Parse JSON file and extract articles.

        Args:
            file_path: Path to JSON file

        Returns:
            List of ImportedArticle objects

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON format is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

        # Validate root structure
        if not isinstance(data, dict):
            raise ValueError("JSON root must be an object")

        if "articles" not in data:
            raise ValueError("JSON must contain 'articles' array")

        if not isinstance(data["articles"], list):
            raise ValueError("'articles' must be an array")

        articles: list[ImportedArticle] = []

        for idx, article_data in enumerate(data["articles"], start=1):
            try:
                article = self._parse_article(article_data, idx)
                articles.append(article)
            except Exception as e:
                logger.warning(
                    "json_article_parse_failed",
                    article_index=idx,
                    error=str(e),
                )
                # Continue parsing (collect errors strategy)
                continue

        logger.info("json_parse_completed", total_articles=len(articles))
        return articles

    def _parse_article(self, data: dict[str, Any], index: int) -> ImportedArticle:
        """Parse a single article from JSON object.

        Args:
            data: Article data dictionary
            index: Article index for error reporting

        Returns:
            ImportedArticle object

        Raises:
            ValueError: If required fields are missing or invalid
        """
        if not isinstance(data, dict):
            raise ValueError(f"Article {index}: must be an object")

        # Required fields
        title = data.get("title", "").strip() if isinstance(data.get("title"), str) else ""
        body = data.get("body", "").strip() if isinstance(data.get("body"), str) else ""
        raw_author_id = str(data.get("author_id", "")).strip()

        if not title:
            raise ValueError(f"Article {index}: title is required")
        if not body:
            raise ValueError(f"Article {index}: body is required")
        if not raw_author_id:
            raise ValueError(f"Article {index}: author_id is required")

        # Normalize author_id with json prefix
        author_id = self._normalize_author_id(raw_author_id, prefix="json")

        # Optional fields
        status = self._parse_status(data.get("status"))
        featured_image_path = data.get("featured_image_path") or None
        additional_images = data.get("additional_images") if isinstance(data.get("additional_images"), list) else None
        cms_article_id = data.get("cms_article_id") or None
        published_url = data.get("published_url") or None
        published_at = self._parse_datetime(data.get("published_at"))

        # Parse metadata (default to empty dict)
        article_metadata = data.get("article_metadata", {})
        if not isinstance(article_metadata, dict):
            article_metadata = {}

        formatting = data.get("formatting", {})
        if not isinstance(formatting, dict):
            formatting = {}

        # Parse SEO metadata if present
        seo_metadata = self._parse_seo_metadata(data.get("seo"))

        # Create ImportedArticle
        article = ImportedArticle(
            title=title,
            body=body,
            author_id=author_id,
            status=status,
            source=self.source_type,
            featured_image_path=featured_image_path,
            additional_images=additional_images,
            cms_article_id=cms_article_id,
            published_url=published_url,
            published_at=published_at,
            article_metadata=article_metadata,
            formatting=formatting,
            seo_metadata=seo_metadata,
            raw_data=data,  # Store original data for debugging
        )

        return article

    def _parse_status(self, status_value: Any) -> ArticleStatus:
        """Parse article status from JSON value.

        Args:
            status_value: Status value from JSON

        Returns:
            ArticleStatus enum value, defaults to IMPORTED
        """
        if not status_value:
            return ArticleStatus.IMPORTED

        status_str = str(status_value).strip().lower()

        # Map status values
        status_map = {
            "imported": ArticleStatus.IMPORTED,
            "draft": ArticleStatus.DRAFT,
            "in-review": ArticleStatus.IN_REVIEW,
            "in_review": ArticleStatus.IN_REVIEW,
            "seo_optimized": ArticleStatus.SEO_OPTIMIZED,
            "ready_to_publish": ArticleStatus.READY_TO_PUBLISH,
            "publishing": ArticleStatus.PUBLISHING,
            "scheduled": ArticleStatus.SCHEDULED,
            "published": ArticleStatus.PUBLISHED,
            "failed": ArticleStatus.FAILED,
        }

        return status_map.get(status_str, ArticleStatus.IMPORTED)

    def _parse_seo_metadata(self, seo_data: Any) -> Optional[dict[str, Any]]:
        """Parse SEO metadata from JSON object.

        Args:
            seo_data: SEO metadata object from JSON

        Returns:
            SEO metadata dictionary or None if not present
        """
        if not seo_data or not isinstance(seo_data, dict):
            return None

        seo_metadata: dict[str, Any] = {}

        # Parse string fields
        if seo_data.get("meta_title"):
            seo_metadata["meta_title"] = str(seo_data["meta_title"]).strip()
        if seo_data.get("meta_description"):
            seo_metadata["meta_description"] = str(seo_data["meta_description"]).strip()
        if seo_data.get("focus_keyword"):
            seo_metadata["focus_keyword"] = str(seo_data["focus_keyword"]).strip()

        # Parse keyword arrays
        if isinstance(seo_data.get("primary_keywords"), list):
            seo_metadata["primary_keywords"] = [
                str(k).strip() for k in seo_data["primary_keywords"] if k
            ]
        if isinstance(seo_data.get("secondary_keywords"), list):
            seo_metadata["secondary_keywords"] = [
                str(k).strip() for k in seo_data["secondary_keywords"] if k
            ]

        # Parse scores (float)
        if seo_data.get("readability_score") is not None:
            try:
                seo_metadata["readability_score"] = float(seo_data["readability_score"])
            except (ValueError, TypeError):
                pass

        if seo_data.get("seo_score") is not None:
            try:
                seo_metadata["seo_score"] = float(seo_data["seo_score"])
            except (ValueError, TypeError):
                pass

        return seo_metadata if seo_metadata else None

    async def validate_article(self, article: ImportedArticle) -> tuple[bool, Optional[str]]:
        """Validate a single article.

        Args:
            article: Article to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate required fields
        if not article.title or len(article.title) < 1:
            return False, "Title is required and must not be empty"

        if not article.body or len(article.body) < 1:
            return False, "Body is required and must not be empty"

        if not article.author_id or article.author_id <= 0:
            return False, "Valid author_id is required"

        # Validate title length
        if len(article.title) > 500:
            return False, "Title must not exceed 500 characters"

        # Validate SEO metadata if present
        if article.seo_metadata:
            validation = self._validate_seo_metadata(article.seo_metadata)
            if not validation[0]:
                return validation

        return True, None

    def _validate_seo_metadata(self, seo_metadata: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate SEO metadata fields.

        Args:
            seo_metadata: SEO metadata dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate meta_title length (50-60 chars)
        if "meta_title" in seo_metadata:
            length = len(seo_metadata["meta_title"])
            if not (50 <= length <= 60):
                return False, f"SEO meta_title must be 50-60 characters (got {length})"

        # Validate meta_description length (150-160 chars)
        if "meta_description" in seo_metadata:
            length = len(seo_metadata["meta_description"])
            if not (150 <= length <= 160):
                return False, f"SEO meta_description must be 150-160 characters (got {length})"

        # Validate primary_keywords count (3-5)
        if "primary_keywords" in seo_metadata:
            count = len(seo_metadata["primary_keywords"])
            if not (3 <= count <= 5):
                return False, f"SEO primary_keywords must have 3-5 items (got {count})"

        # Validate secondary_keywords count (5-10)
        if "secondary_keywords" in seo_metadata:
            count = len(seo_metadata["secondary_keywords"])
            if not (5 <= count <= 10):
                return False, f"SEO secondary_keywords must have 5-10 items (got {count})"

        # Validate scores (0-100)
        for score_field in ["readability_score", "seo_score"]:
            if score_field in seo_metadata:
                score = seo_metadata[score_field]
                if not (0 <= score <= 100):
                    return False, f"SEO {score_field} must be between 0 and 100 (got {score})"

        return True, None
