"""Base classes for article importers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.models import ArticleStatus


@dataclass
class ImportedArticle:
    """Data structure for a single imported article."""

    title: str
    body: str
    author_id: int

    # Optional fields
    status: ArticleStatus = ArticleStatus.IMPORTED
    source: str = "csv_import"
    featured_image_path: str | None = None
    additional_images: list[str] | None = None
    cms_article_id: str | None = None
    published_url: str | None = None
    published_at: datetime | None = None
    article_metadata: dict[str, Any] = field(default_factory=dict)
    formatting: dict[str, Any] = field(default_factory=dict)

    # SEO metadata (optional)
    seo_metadata: dict[str, Any] | None = None

    # Raw data for debugging
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportError:
    """Error information for failed import."""

    row_number: int
    error_message: str
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportResult:
    """Result of an import operation."""

    total_records: int
    successful_imports: int
    failed_imports: int
    errors: list[ImportError] = field(default_factory=list)
    imported_article_ids: list[int] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_records == 0:
            return 0.0
        return (self.successful_imports / self.total_records) * 100

    def add_success(self, article_id: int) -> None:
        """Record a successful import."""
        self.successful_imports += 1
        self.imported_article_ids.append(article_id)

    def add_error(self, row_number: int, error_message: str, raw_data: dict[str, Any] = None) -> None:
        """Record a failed import."""
        self.failed_imports += 1
        self.errors.append(
            ImportError(
                row_number=row_number,
                error_message=error_message,
                raw_data=raw_data or {},
            )
        )


class ArticleImporter(ABC):
    """Abstract base class for article importers."""

    def __init__(self, source_type: str) -> None:
        """Initialize importer.

        Args:
            source_type: Source identifier (csv_import, json_import, wordpress_export)
        """
        self.source_type = source_type

    @abstractmethod
    async def parse_file(self, file_path: str) -> list[ImportedArticle]:
        """Parse file and extract articles.

        Args:
            file_path: Path to the file to import

        Returns:
            List of ImportedArticle objects

        Raises:
            ValueError: If file format is invalid
            FileNotFoundError: If file doesn't exist
        """
        pass

    @abstractmethod
    async def validate_article(self, article: ImportedArticle) -> tuple[bool, str | None]:
        """Validate a single article.

        Args:
            article: Article to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    def _normalize_author_id(self, raw_author_id: Any, prefix: str = "imported") -> int:
        """Normalize author ID with prefix to avoid conflicts.

        Args:
            raw_author_id: Raw author ID from import file
            prefix: Prefix to add (default: "imported")

        Returns:
            Normalized author ID as integer

        Example:
            _normalize_author_id("123", "csv") -> uses hash to create unique ID
        """
        # Create a deterministic hash from prefix + author_id
        # This ensures same author ID always maps to same internal ID
        combined = f"{prefix}_{raw_author_id}"
        # Use hash to create integer ID (take absolute value and modulo to keep reasonable)
        return abs(hash(combined)) % 1_000_000_000

    def _parse_datetime(self, value: Any) -> datetime | None:
        """Parse datetime from various formats.

        Args:
            value: Value to parse (string, datetime, or None)

        Returns:
            datetime object or None
        """
        if value is None or value == "":
            return None

        if isinstance(value, datetime):
            return value

        # Try common datetime formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue

        # If all formats fail, return None
        return None
