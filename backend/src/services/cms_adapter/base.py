"""Abstract base class for CMS platform adapters."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ArticleMetadata(BaseModel):
    """Metadata for article publishing."""

    title: str
    body: str
    excerpt: str | None = None
    featured_image_url: str | None = None
    tags: list[str] = []
    categories: list[str] = []
    status: str = "draft"  # draft, published, scheduled
    scheduled_time: str | None = None
    author_id: str | None = None
    custom_fields: dict[str, Any] = {}


class PublishResult(BaseModel):
    """Result of article publishing operation."""

    success: bool
    cms_article_id: str | None = None
    url: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = {}


class CMSAdapter(ABC):
    """Abstract base class for CMS platform integration.

    This adapter pattern allows the automation system to work with
    multiple CMS platforms (WordPress, Strapi, Contentful, etc.)
    without changing the core business logic.
    """

    def __init__(self, base_url: str, credentials: dict[str, str]) -> None:
        """Initialize CMS adapter.

        Args:
            base_url: Base URL of the CMS instance
            credentials: Authentication credentials (API key, username/password, etc.)
        """
        self.base_url = base_url.rstrip("/")
        self.credentials = credentials

    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the CMS platform.

        Returns:
            bool: True if authentication successful

        Raises:
            Exception: If authentication fails
        """
        pass

    @abstractmethod
    async def publish_article(self, metadata: ArticleMetadata) -> PublishResult:
        """Publish an article to the CMS.

        Args:
            metadata: Article metadata and content

        Returns:
            PublishResult: Publishing result with CMS article ID

        Raises:
            Exception: If publishing fails
        """
        pass

    @abstractmethod
    async def update_article(
        self, cms_article_id: str, metadata: ArticleMetadata
    ) -> PublishResult:
        """Update an existing article in the CMS.

        Args:
            cms_article_id: CMS platform's article ID
            metadata: Updated article metadata and content

        Returns:
            PublishResult: Update result

        Raises:
            Exception: If update fails
        """
        pass

    @abstractmethod
    async def delete_article(self, cms_article_id: str) -> bool:
        """Delete an article from the CMS.

        Args:
            cms_article_id: CMS platform's article ID

        Returns:
            bool: True if deletion successful

        Raises:
            Exception: If deletion fails
        """
        pass

    @abstractmethod
    async def get_article(self, cms_article_id: str) -> dict[str, Any]:
        """Get article details from the CMS.

        Args:
            cms_article_id: CMS platform's article ID

        Returns:
            dict: Article data from CMS

        Raises:
            Exception: If retrieval fails
        """
        pass

    @abstractmethod
    async def create_tag(self, tag_name: str) -> str:
        """Create a new tag in the CMS.

        Args:
            tag_name: Tag name to create

        Returns:
            str: CMS tag ID

        Raises:
            Exception: If tag creation fails
        """
        pass

    @abstractmethod
    async def get_tags(self) -> list[dict[str, Any]]:
        """Get all tags from the CMS.

        Returns:
            list: List of tag objects from CMS

        Raises:
            Exception: If retrieval fails
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if CMS is reachable and responsive.

        Returns:
            bool: True if CMS is healthy

        Raises:
            Exception: If health check fails
        """
        pass
