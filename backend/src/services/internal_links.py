"""Internal Link Service for matching related articles (Phase 12).

This service integrates with the Supabase Edge Function to find semantically
related articles from the health article database for internal linking.
"""

import logging
import os
from typing import Any

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RelatedArticleMatch(BaseModel):
    """A matched related article from Supabase."""

    article_id: str
    title: str
    title_main: str | None = None
    url: str
    excerpt: str | None = None
    similarity: float
    match_type: str
    ai_keywords: list[str] = Field(default_factory=list)
    matched_keywords: list[str] | None = None


class MatchResult(BaseModel):
    """Result from the internal link matching API."""

    success: bool
    matches: list[RelatedArticleMatch] = Field(default_factory=list)
    stats: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class InternalLinkService:
    """Service for matching related articles via Supabase Edge Function.

    Uses the match-internal-links Edge Function to find semantically related
    articles based on title, keywords, and optional content.
    """

    DEFAULT_SUPABASE_URL = "https://twsbhjmlmspjwfystpti.supabase.co"
    MATCH_ENDPOINT = "/functions/v1/match-internal-links"
    DEFAULT_TIMEOUT = 30.0  # seconds
    DEFAULT_LIMIT = 5

    def __init__(
        self,
        supabase_url: str | None = None,
        service_role_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """Initialize the internal link service.

        Args:
            supabase_url: Supabase project URL. Defaults to env SUPABASE_URL.
            service_role_key: Supabase service role key. Defaults to env SUPABASE_SERVICE_ROLE_KEY.
            timeout: HTTP request timeout in seconds.
        """
        self.supabase_url = supabase_url or os.getenv(
            "SUPABASE_URL", self.DEFAULT_SUPABASE_URL
        )
        self.service_role_key = service_role_key or os.getenv(
            "SUPABASE_SERVICE_ROLE_KEY"
        )
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

        if not self.service_role_key:
            logger.warning(
                "SUPABASE_SERVICE_ROLE_KEY not configured. "
                "Internal link matching will be disabled."
            )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    @property
    def is_configured(self) -> bool:
        """Check if the service is properly configured."""
        return bool(self.service_role_key)

    async def match_related_articles(
        self,
        title: str,
        keywords: list[str] | None = None,
        content: str | None = None,
        article_id: str | None = None,
        limit: int = DEFAULT_LIMIT,
        title_threshold: float = 0.7,
        include_content_match: bool = False,
    ) -> MatchResult:
        """Find related articles based on title and keywords.

        Args:
            title: Article title for semantic matching.
            keywords: Optional SEO keywords to enhance matching.
            content: Optional content excerpt for deep matching.
            article_id: Optional article ID to exclude (avoid self-matching).
            limit: Maximum number of matches to return.
            title_threshold: Minimum similarity threshold (0-1).
            include_content_match: Whether to include content-based matching.

        Returns:
            MatchResult with related articles and statistics.
        """
        if not self.is_configured:
            logger.warning("Internal link service not configured, skipping match")
            return MatchResult(
                success=False,
                error="Service not configured: SUPABASE_SERVICE_ROLE_KEY missing",
            )

        if not title or not title.strip():
            return MatchResult(
                success=False,
                error="Title is required for matching",
            )

        try:
            client = await self._get_client()

            # Build request payload
            payload: dict[str, Any] = {
                "title": title.strip(),
                "limit": limit,
                "title_threshold": title_threshold,
            }

            if keywords:
                payload["keywords"] = [k.strip() for k in keywords if k.strip()]

            if content and include_content_match:
                # Truncate content to avoid token limits
                payload["content"] = content[:8000]
                payload["include_content_match"] = True

            if article_id:
                payload["article_id"] = article_id

            # Make API request
            url = f"{self.supabase_url}{self.MATCH_ENDPOINT}"
            headers = {
                "Authorization": f"Bearer {self.service_role_key}",
            }

            logger.info(
                f"Matching related articles for title: {title[:50]}... "
                f"(keywords: {len(keywords or [])})"
            )

            response = await client.post(url, json=payload, headers=headers)

            if response.status_code != 200:
                error_text = response.text
                logger.error(
                    f"Internal link API error: {response.status_code} - {error_text}"
                )
                return MatchResult(
                    success=False,
                    error=f"API error: {response.status_code}",
                )

            data = response.json()

            if not data.get("success"):
                return MatchResult(
                    success=False,
                    error=data.get("error", "Unknown error"),
                )

            # Parse matches
            matches = []
            for match_data in data.get("matches", []):
                try:
                    match = RelatedArticleMatch(
                        article_id=match_data["article_id"],
                        title=match_data["title"],
                        title_main=match_data.get("title_main"),
                        url=match_data["url"],
                        excerpt=match_data.get("excerpt"),
                        similarity=match_data["similarity"],
                        match_type=match_data["match_type"],
                        ai_keywords=match_data.get("ai_keywords", []),
                        matched_keywords=match_data.get("matched_keywords"),
                    )
                    matches.append(match)
                except Exception as e:
                    logger.warning(f"Failed to parse match: {e}")
                    continue

            logger.info(
                f"Found {len(matches)} related articles "
                f"(semantic: {data.get('stats', {}).get('semanticMatches', 0)}, "
                f"keyword: {data.get('stats', {}).get('keywordMatches', 0)})"
            )

            return MatchResult(
                success=True,
                matches=matches,
                stats=data.get("stats", {}),
            )

        except httpx.TimeoutException:
            logger.error("Internal link API timeout")
            return MatchResult(
                success=False,
                error="API request timeout",
            )
        except httpx.RequestError as e:
            logger.error(f"Internal link API request error: {e}")
            return MatchResult(
                success=False,
                error=f"Request error: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Unexpected error in internal link matching: {e}")
            return MatchResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
            )


# Singleton instance for easy access
_internal_link_service: InternalLinkService | None = None


def get_internal_link_service() -> InternalLinkService:
    """Get or create the internal link service singleton."""
    global _internal_link_service
    if _internal_link_service is None:
        _internal_link_service = InternalLinkService()
    return _internal_link_service


async def match_related_articles(
    title: str,
    keywords: list[str] | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Convenience function to match related articles.

    Args:
        title: Article title for matching.
        keywords: Optional keywords to enhance matching.
        limit: Maximum number of matches.

    Returns:
        List of related article dictionaries.
    """
    service = get_internal_link_service()
    result = await service.match_related_articles(
        title=title,
        keywords=keywords,
        limit=limit,
    )

    if not result.success:
        logger.warning(f"Related article matching failed: {result.error}")
        return []

    return [match.model_dump() for match in result.matches]
