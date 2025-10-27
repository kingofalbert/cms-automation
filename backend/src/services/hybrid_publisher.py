"""Hybrid publishing service - intelligently choose between Computer Use and Playwright.

This service automatically selects the best publishing method based on:
- Article complexity
- Available configuration
- Cost preferences
- Publishing volume
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from src.api.schemas.seo import SEOMetadata
from src.config import get_logger, get_settings
from src.services.computer_use_cms import ComputerUseCMSService
from src.services.providers.playwright_wordpress_publisher import (
    create_playwright_publisher,
)

logger = get_logger(__name__)
settings = get_settings()


class PublishingStrategy(str, Enum):
    """Publishing strategy options."""

    AUTO = "auto"  # Automatically choose best method
    COMPUTER_USE_ONLY = "computer_use"  # Always use Computer Use (AI)
    PLAYWRIGHT_ONLY = "playwright"  # Always use Playwright (free)
    COST_OPTIMIZED = "cost_optimized"  # Prefer Playwright, fallback to Computer Use
    QUALITY_OPTIMIZED = "quality_optimized"  # Prefer Computer Use for reliability


class HybridPublisher:
    """Intelligent publisher that chooses between Computer Use and Playwright.

    Decision factors:
    1. Playwright config availability
    2. Article complexity (custom fields, special formatting)
    3. Monthly publishing volume
    4. Cost budget
    5. User preference
    """

    def __init__(
        self,
        strategy: PublishingStrategy = PublishingStrategy.AUTO,
        playwright_config_path: Optional[str] = None,
        cost_budget_usd: Optional[float] = None,
    ) -> None:
        """Initialize hybrid publisher.

        Args:
            strategy: Publishing strategy to use
            playwright_config_path: Path to Playwright config (if available)
            cost_budget_usd: Monthly cost budget in USD
        """
        self.strategy = strategy
        self.playwright_config_path = playwright_config_path
        self.cost_budget_usd = cost_budget_usd

        # Check if Playwright is configured
        self.playwright_available = self._check_playwright_config()

        # Initialize publishers
        self.computer_use_service = ComputerUseCMSService()

        logger.info(
            "hybrid_publisher_initialized",
            strategy=strategy,
            playwright_available=self.playwright_available,
        )

    def _check_playwright_config(self) -> bool:
        """Check if Playwright configuration is available.

        Returns:
            True if Playwright can be used
        """
        if not self.playwright_config_path:
            return False

        try:
            import os

            return os.path.exists(self.playwright_config_path)
        except Exception:
            return False

    async def publish_article(
        self,
        cms_url: str,
        username: str,
        password: str,
        article_title: str,
        article_body: str,
        seo_data: SEOMetadata,
        article_images: List[Dict] = None,
        article_metadata: Dict = None,
    ) -> Dict[str, Any]:
        """Publish article using best available method.

        Args:
            cms_url: WordPress site URL
            username: WordPress username
            password: WordPress password
            article_title: Article title
            article_body: Article content
            seo_data: SEO metadata
            article_images: List of article images
            article_metadata: Additional article metadata

        Returns:
            Publishing result with method used
        """
        # Determine which method to use
        use_method = self._decide_publishing_method(
            article_metadata=article_metadata or {},
            has_images=bool(article_images),
        )

        logger.info(
            "hybrid_publish_started",
            method=use_method,
            title=article_title[:50],
            strategy=self.strategy,
        )

        try:
            if use_method == "playwright":
                result = await self._publish_with_playwright(
                    cms_url=cms_url,
                    username=username,
                    password=password,
                    article_title=article_title,
                    article_body=article_body,
                    seo_data=seo_data,
                    article_images=article_images,
                )
            else:  # computer_use
                result = await self._publish_with_computer_use(
                    cms_url=cms_url,
                    username=username,
                    password=password,
                    article_title=article_title,
                    article_body=article_body,
                    seo_data=seo_data,
                    article_images=article_images,
                )

            # Add method to result
            result["publishing_method"] = use_method

            logger.info(
                "hybrid_publish_completed",
                method=use_method,
                success=result.get("success"),
            )

            return result

        except Exception as e:
            logger.error(
                "hybrid_publish_failed",
                method=use_method,
                error=str(e),
                exc_info=True,
            )

            # Try fallback if available
            if self.strategy == PublishingStrategy.COST_OPTIMIZED and use_method == "playwright":
                logger.info("attempting_fallback_to_computer_use")
                try:
                    result = await self._publish_with_computer_use(
                        cms_url=cms_url,
                        username=username,
                        password=password,
                        article_title=article_title,
                        article_body=article_body,
                        seo_data=seo_data,
                        article_images=article_images,
                    )
                    result["publishing_method"] = "computer_use_fallback"
                    return result
                except Exception as fallback_error:
                    logger.error(
                        "fallback_also_failed",
                        error=str(fallback_error),
                    )

            return {
                "success": False,
                "error": str(e),
                "publishing_method": use_method,
            }

    def _decide_publishing_method(
        self,
        article_metadata: Dict,
        has_images: bool,
    ) -> str:
        """Decide which publishing method to use.

        Args:
            article_metadata: Article metadata
            has_images: Whether article has images

        Returns:
            "playwright" or "computer_use"
        """
        # Force specific method if strategy requires it
        if self.strategy == PublishingStrategy.PLAYWRIGHT_ONLY:
            if not self.playwright_available:
                logger.warning(
                    "playwright_required_but_not_available",
                    fallback="computer_use",
                )
                return "computer_use"
            return "playwright"

        if self.strategy == PublishingStrategy.COMPUTER_USE_ONLY:
            return "computer_use"

        # For AUTO and optimized strategies, make intelligent decision
        if not self.playwright_available:
            logger.debug("playwright_not_configured_using_computer_use")
            return "computer_use"

        # Check article complexity
        is_complex = self._is_article_complex(article_metadata)

        if self.strategy == PublishingStrategy.QUALITY_OPTIMIZED:
            # Prefer Computer Use for better reliability
            if is_complex:
                logger.debug("complex_article_using_computer_use")
                return "computer_use"
            # Simple articles can use Playwright
            return "playwright"

        if self.strategy == PublishingStrategy.COST_OPTIMIZED:
            # Prefer Playwright to save cost
            if is_complex:
                # Complex articles need Computer Use intelligence
                logger.debug("complex_article_requires_computer_use")
                return "computer_use"
            # Simple articles use free Playwright
            return "playwright"

        # AUTO strategy (default)
        if is_complex:
            return "computer_use"

        # Simple articles use Playwright if available
        return "playwright"

    def _is_article_complex(self, metadata: Dict) -> bool:
        """Determine if article is complex and needs AI intelligence.

        Args:
            metadata: Article metadata

        Returns:
            True if article is complex
        """
        # Check for complexity indicators
        has_custom_fields = bool(metadata.get("custom_fields"))
        has_advanced_formatting = bool(metadata.get("advanced_formatting"))
        has_shortcodes = bool(metadata.get("shortcodes"))
        is_long_form = metadata.get("word_count", 0) > 3000

        return any([
            has_custom_fields,
            has_advanced_formatting,
            has_shortcodes,
            is_long_form,
        ])

    async def _publish_with_playwright(
        self,
        cms_url: str,
        username: str,
        password: str,
        article_title: str,
        article_body: str,
        seo_data: SEOMetadata,
        article_images: List[Dict],
    ) -> Dict[str, Any]:
        """Publish using Playwright (free).

        Args:
            cms_url: WordPress URL
            username: Username
            password: Password
            article_title: Title
            article_body: Body
            seo_data: SEO data
            article_images: Images

        Returns:
            Publishing result
        """
        logger.info("publishing_with_playwright")

        playwright_publisher = await create_playwright_publisher(
            self.playwright_config_path
        )

        result = await playwright_publisher.publish_article(
            cms_url=cms_url,
            username=username,
            password=password,
            article_title=article_title,
            article_body=article_body,
            seo_data=seo_data,
            article_images=article_images or [],
            headless=True,
        )

        return result

    async def _publish_with_computer_use(
        self,
        cms_url: str,
        username: str,
        password: str,
        article_title: str,
        article_body: str,
        seo_data: SEOMetadata,
        article_images: List[Dict],
    ) -> Dict[str, Any]:
        """Publish using Computer Use (paid, intelligent).

        Args:
            cms_url: WordPress URL
            username: Username
            password: Password
            article_title: Title
            article_body: Body
            seo_data: SEO data
            article_images: Images

        Returns:
            Publishing result
        """
        logger.info("publishing_with_computer_use")

        result = await self.computer_use_service.publish_article_with_seo(
            article_title=article_title,
            article_body=article_body,
            seo_data=seo_data,
            cms_url=cms_url,
            cms_username=username,
            cms_password=password,
            article_images=article_images or [],
        )

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get publishing statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "strategy": self.strategy,
            "playwright_available": self.playwright_available,
            "cost_budget_usd": self.cost_budget_usd,
        }


async def create_hybrid_publisher(
    strategy: str = "auto",
    playwright_config_path: Optional[str] = None,
) -> HybridPublisher:
    """Factory function to create hybrid publisher.

    Args:
        strategy: Publishing strategy (auto, computer_use, playwright, etc.)
        playwright_config_path: Path to Playwright configuration

    Returns:
        HybridPublisher instance
    """
    strategy_enum = PublishingStrategy(strategy)

    return HybridPublisher(
        strategy=strategy_enum,
        playwright_config_path=playwright_config_path,
    )
