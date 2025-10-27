"""CSV article importer."""

import csv
from pathlib import Path
from typing import Any, Optional

from src.config import get_logger
from src.models import ArticleStatus
from src.services.article_importer.base import ArticleImporter, ImportedArticle

logger = get_logger(__name__)


class CSVImporter(ArticleImporter):
    """Import articles from CSV files.

    Expected CSV format:
        title,body,author_id[,status,featured_image_path,published_at,...]

    Required fields:
        - title: Article title
        - body: Article content
        - author_id: Author identifier (will be prefixed to avoid conflicts)

    Optional fields:
        - status: Article status (defaults to IMPORTED)
        - featured_image_path: Path to featured image
        - additional_images: JSON array of image paths
        - cms_article_id: CMS platform article ID
        - published_url: Public URL
        - published_at: Publication timestamp
        - article_metadata: JSON object with metadata
        - formatting: JSON object with formatting preferences

    SEO Metadata (optional, with seo_ prefix):
        - seo_meta_title: SEO title (50-60 chars)
        - seo_meta_description: SEO description (150-160 chars)
        - seo_focus_keyword: Primary keyword
        - seo_primary_keywords: Comma-separated list (3-5 keywords)
        - seo_secondary_keywords: Comma-separated list (5-10 keywords)
        - seo_readability_score: Score 0-100
        - seo_seo_score: Score 0-100
    """

    def __init__(self) -> None:
        """Initialize CSV importer."""
        super().__init__(source_type="csv_import")

    async def parse_file(self, file_path: str) -> list[ImportedArticle]:
        """Parse CSV file and extract articles.

        Args:
            file_path: Path to CSV file

        Returns:
            List of ImportedArticle objects

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If CSV format is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        articles: list[ImportedArticle] = []

        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                # Validate required columns
                required_columns = {"title", "body", "author_id"}
                if not required_columns.issubset(set(reader.fieldnames or [])):
                    missing = required_columns - set(reader.fieldnames or [])
                    raise ValueError(f"CSV missing required columns: {missing}")

                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    try:
                        article = self._parse_row(row, row_num)
                        articles.append(article)
                    except Exception as e:
                        logger.warning(
                            "csv_row_parse_failed",
                            row_number=row_num,
                            error=str(e),
                        )
                        # Continue parsing (collect errors strategy)
                        continue

        except csv.Error as e:
            raise ValueError(f"Invalid CSV format: {e}")

        logger.info("csv_parse_completed", total_articles=len(articles))
        return articles

    def _parse_row(self, row: dict[str, str], row_num: int) -> ImportedArticle:
        """Parse a single CSV row into ImportedArticle.

        Args:
            row: CSV row as dictionary
            row_num: Row number for error reporting

        Returns:
            ImportedArticle object

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Required fields
        title = row.get("title", "").strip()
        body = row.get("body", "").strip()
        raw_author_id = row.get("author_id", "").strip()

        if not title:
            raise ValueError(f"Row {row_num}: title is required")
        if not body:
            raise ValueError(f"Row {row_num}: body is required")
        if not raw_author_id:
            raise ValueError(f"Row {row_num}: author_id is required")

        # Normalize author_id with csv prefix
        author_id = self._normalize_author_id(raw_author_id, prefix="csv")

        # Optional fields
        status = self._parse_status(row.get("status"))
        featured_image_path = row.get("featured_image_path") or None
        published_at = self._parse_datetime(row.get("published_at"))

        # Parse SEO metadata if present
        seo_metadata = self._parse_seo_metadata(row)

        # Create ImportedArticle
        article = ImportedArticle(
            title=title,
            body=body,
            author_id=author_id,
            status=status,
            source=self.source_type,
            featured_image_path=featured_image_path,
            published_at=published_at,
            seo_metadata=seo_metadata,
            raw_data=dict(row),  # Store original row for debugging
        )

        return article

    def _parse_status(self, status_str: Optional[str]) -> ArticleStatus:
        """Parse article status from string.

        Args:
            status_str: Status string from CSV

        Returns:
            ArticleStatus enum value, defaults to IMPORTED
        """
        if not status_str:
            return ArticleStatus.IMPORTED

        status_str = status_str.strip().lower()

        # Map common status values
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

    def _parse_seo_metadata(self, row: dict[str, str]) -> Optional[dict[str, Any]]:
        """Parse SEO metadata from CSV row.

        Args:
            row: CSV row dictionary

        Returns:
            SEO metadata dictionary or None if no SEO fields present
        """
        seo_fields = {
            "seo_meta_title",
            "seo_meta_description",
            "seo_focus_keyword",
            "seo_primary_keywords",
            "seo_secondary_keywords",
            "seo_readability_score",
            "seo_seo_score",
        }

        # Check if any SEO field is present
        has_seo = any(field in row and row[field] for field in seo_fields)
        if not has_seo:
            return None

        seo_metadata: dict[str, Any] = {}

        # Parse string fields
        if row.get("seo_meta_title"):
            seo_metadata["meta_title"] = row["seo_meta_title"].strip()
        if row.get("seo_meta_description"):
            seo_metadata["meta_description"] = row["seo_meta_description"].strip()
        if row.get("seo_focus_keyword"):
            seo_metadata["focus_keyword"] = row["seo_focus_keyword"].strip()

        # Parse keyword arrays (comma-separated)
        if row.get("seo_primary_keywords"):
            seo_metadata["primary_keywords"] = [
                k.strip() for k in row["seo_primary_keywords"].split(",") if k.strip()
            ]
        if row.get("seo_secondary_keywords"):
            seo_metadata["secondary_keywords"] = [
                k.strip() for k in row["seo_secondary_keywords"].split(",") if k.strip()
            ]

        # Parse scores (float)
        if row.get("seo_readability_score"):
            try:
                seo_metadata["readability_score"] = float(row["seo_readability_score"])
            except ValueError:
                pass

        if row.get("seo_seo_score"):
            try:
                seo_metadata["seo_score"] = float(row["seo_seo_score"])
            except ValueError:
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
