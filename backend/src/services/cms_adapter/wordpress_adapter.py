"""WordPress REST API adapter implementation."""

from typing import Any

import httpx

from src.config.logging import get_logger
from src.services.cms_adapter.auth import CMSAuthHandler
from src.services.cms_adapter.base import (
    ArticleMetadata,
    CMSAdapter,
    PublishResult,
)

logger = get_logger(__name__)


class WordPressAdapter(CMSAdapter):
    """WordPress CMS adapter using REST API."""

    def __init__(
        self,
        base_url: str,
        credentials: dict[str, str],
        http_auth: tuple[str, str] | None = None,
    ) -> None:
        """Initialize WordPress adapter.

        Args:
            base_url: WordPress site URL
            credentials: WordPress credentials (username, application_password)
            http_auth: Optional HTTP Basic Auth tuple (username, password) for site-level auth
        """
        super().__init__(base_url, credentials)
        self.api_base = f"{self.base_url}/wp-json/wp/v2"
        self.auth_handler = CMSAuthHandler("wordpress", base_url, credentials)
        self.http_auth = http_auth
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client.

        Returns:
            httpx.AsyncClient: HTTP client instance
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers=self.auth_handler.get_headers(),
                auth=self.http_auth,  # Site-level HTTP Basic Auth
            )
        return self._client

    async def authenticate(self) -> bool:
        """Verify WordPress authentication.

        Returns:
            bool: True if authentication successful
        """
        return await self.auth_handler.verify_auth()

    async def publish_article(self, metadata: ArticleMetadata) -> PublishResult:
        """Publish article to WordPress.

        Args:
            metadata: Article metadata and content

        Returns:
            PublishResult: Publishing result
        """
        client = await self._get_client()

        try:
            # Prepare post data
            post_data = {
                "title": metadata.title,
                "content": metadata.body,
                "excerpt": metadata.excerpt or "",
                "status": metadata.status,
            }

            # Add tags if provided (skip for drafts to avoid 404 errors on some WP installations)
            if metadata.tags and metadata.status != "draft":
                try:
                    # Get or create tag IDs
                    tag_ids = await self._get_or_create_tag_ids(metadata.tags)
                    post_data["tags"] = tag_ids
                except Exception as e:
                    logger.warning("wordpress_tags_skip", error=str(e))

            # Add categories if provided (skip for drafts to avoid 404 errors on some WP installations)
            if metadata.categories and metadata.status != "draft":
                try:
                    category_ids = await self._get_or_create_category_ids(
                        metadata.categories
                    )
                    post_data["categories"] = category_ids
                except Exception as e:
                    logger.warning("wordpress_categories_skip", error=str(e))

            # Create post
            response = await client.post(f"{self.api_base}/posts", json=post_data)

            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(
                    "wordpress_article_published",
                    post_id=result["id"],
                    url=result["link"],
                )
                return PublishResult(
                    success=True,
                    cms_article_id=str(result["id"]),
                    url=result["link"],
                    metadata={"status": result["status"]},
                )
            else:
                logger.error(
                    "wordpress_publish_failed",
                    status_code=response.status_code,
                    response=response.text,
                )
                return PublishResult(
                    success=False,
                    error=f"WordPress API error: {response.status_code}",
                )

        except Exception as e:
            logger.error("wordpress_publish_exception", error=str(e), exc_info=True)
            return PublishResult(success=False, error=str(e))

    async def update_article(
        self, cms_article_id: str, metadata: ArticleMetadata
    ) -> PublishResult:
        """Update WordPress article.

        Args:
            cms_article_id: WordPress post ID
            metadata: Updated metadata

        Returns:
            PublishResult: Update result
        """
        client = await self._get_client()

        try:
            post_data = {
                "title": metadata.title,
                "content": metadata.body,
                "excerpt": metadata.excerpt or "",
                "status": metadata.status,
            }

            response = await client.post(
                f"{self.api_base}/posts/{cms_article_id}", json=post_data
            )

            if response.status_code == 200:
                result = response.json()
                return PublishResult(
                    success=True,
                    cms_article_id=str(result["id"]),
                    url=result["link"],
                )
            else:
                return PublishResult(
                    success=False,
                    error=f"WordPress API error: {response.status_code}",
                )

        except Exception as e:
            logger.error("wordpress_update_exception", error=str(e), exc_info=True)
            return PublishResult(success=False, error=str(e))

    async def delete_article(self, cms_article_id: str) -> bool:
        """Delete WordPress article.

        Args:
            cms_article_id: WordPress post ID

        Returns:
            bool: True if deletion successful
        """
        client = await self._get_client()

        try:
            response = await client.delete(f"{self.api_base}/posts/{cms_article_id}")
            return response.status_code == 200

        except Exception as e:
            logger.error("wordpress_delete_exception", error=str(e), exc_info=True)
            return False

    async def get_article(self, cms_article_id: str) -> dict[str, Any]:
        """Get WordPress article details.

        Args:
            cms_article_id: WordPress post ID

        Returns:
            dict: Article data
        """
        client = await self._get_client()
        response = await client.get(f"{self.api_base}/posts/{cms_article_id}")
        response.raise_for_status()
        return response.json()

    async def create_tag(self, tag_name: str) -> str:
        """Create WordPress tag.

        Args:
            tag_name: Tag name

        Returns:
            str: WordPress tag ID
        """
        client = await self._get_client()

        try:
            response = await client.post(
                f"{self.api_base}/tags", json={"name": tag_name}
            )

            if response.status_code in [200, 201]:
                result = response.json()
                return str(result["id"])
            else:
                raise Exception(f"Failed to create tag: {response.text}")

        except Exception as e:
            logger.error("wordpress_create_tag_exception", error=str(e), exc_info=True)
            raise

    async def get_tags(self) -> list[dict[str, Any]]:
        """Get all WordPress tags.

        Returns:
            list: List of tag objects
        """
        client = await self._get_client()
        response = await client.get(f"{self.api_base}/tags", params={"per_page": 100})
        response.raise_for_status()
        return response.json()

    async def _get_or_create_tag_ids(self, tag_names: list[str]) -> list[int]:
        """Get or create tag IDs for tag names.

        Args:
            tag_names: List of tag names

        Returns:
            list: List of tag IDs
        """
        existing_tags = await self.get_tags()
        tag_map = {tag["name"].lower(): tag["id"] for tag in existing_tags}

        tag_ids = []
        for name in tag_names:
            if name.lower() in tag_map:
                tag_ids.append(tag_map[name.lower()])
            else:
                # Create new tag
                tag_id = await self.create_tag(name)
                tag_ids.append(int(tag_id))

        return tag_ids

    async def _get_or_create_category_ids(
        self, category_names: list[str]
    ) -> list[int]:
        """Get or create category IDs.

        Args:
            category_names: List of category names

        Returns:
            list: List of category IDs
        """
        client = await self._get_client()

        # Get existing categories
        response = await client.get(
            f"{self.api_base}/categories", params={"per_page": 100}
        )
        existing_categories = response.json()
        category_map = {cat["name"].lower(): cat["id"] for cat in existing_categories}

        category_ids = []
        for name in category_names:
            if name.lower() in category_map:
                category_ids.append(category_map[name.lower()])
            else:
                # Create new category
                response = await client.post(
                    f"{self.api_base}/categories", json={"name": name}
                )
                if response.status_code in [200, 201]:
                    category_ids.append(response.json()["id"])

        return category_ids

    async def health_check(self) -> bool:
        """Check WordPress health.

        Returns:
            bool: True if WordPress is healthy
        """
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/wp-json")
            return response.status_code == 200

        except Exception as e:
            logger.error("wordpress_health_check_failed", error=str(e))
            return False

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
