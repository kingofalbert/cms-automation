"""CMS adapter factory for creating platform-specific adapters."""


from src.config.logging import get_logger
from src.config.settings import get_settings
from src.services.cms_adapter.base import CMSAdapter
from src.services.cms_adapter.wordpress_adapter import WordPressAdapter

logger = get_logger(__name__)


class CMSAdapterFactory:
    """Factory for creating CMS adapter instances."""

    _adapters: dict[str, type[CMSAdapter]] = {
        "wordpress": WordPressAdapter,
        # Add more adapters as implemented:
        # "strapi": StratoAdapter,
        # "contentful": ContentfulAdapter,
        # "ghost": GhostAdapter,
    }

    @classmethod
    def create(
        cls,
        cms_type: str | None = None,
        base_url: str | None = None,
        credentials: dict[str, str] | None = None,
    ) -> CMSAdapter:
        """Create a CMS adapter instance.

        Args:
            cms_type: CMS platform type (defaults to settings.CMS_TYPE)
            base_url: CMS base URL (defaults to settings.CMS_BASE_URL)
            credentials: Authentication credentials (defaults from settings)

        Returns:
            CMSAdapter: CMS adapter instance

        Raises:
            ValueError: If CMS type is not supported
        """
        settings = get_settings()

        # Use settings as defaults
        cms_type = (cms_type or settings.CMS_TYPE).lower()
        base_url = base_url or settings.CMS_BASE_URL

        if credentials is None:
            credentials = cls._get_credentials_from_settings(cms_type)

        # Get adapter class
        adapter_class = cls._adapters.get(cms_type)
        if adapter_class is None:
            raise ValueError(
                f"Unsupported CMS type: {cms_type}. "
                f"Supported types: {', '.join(cls._adapters.keys())}"
            )

        logger.info(
            "cms_adapter_created",
            cms_type=cms_type,
            base_url=base_url,
        )

        return adapter_class(base_url, credentials)

    @classmethod
    def _get_credentials_from_settings(cls, cms_type: str) -> dict[str, str]:
        """Get CMS credentials from settings.

        Args:
            cms_type: CMS platform type

        Returns:
            dict: Credentials dictionary
        """
        settings = get_settings()

        if cms_type == "wordpress":
            return {
                "username": settings.CMS_USERNAME,
                "application_password": settings.CMS_APPLICATION_PASSWORD,
            }
        else:
            # For token-based auth platforms
            return {
                "api_token": settings.CMS_API_TOKEN,
            }

    @classmethod
    def register_adapter(cls, cms_type: str, adapter_class: type[CMSAdapter]) -> None:
        """Register a new CMS adapter.

        Args:
            cms_type: CMS platform type identifier
            adapter_class: Adapter class implementing CMSAdapter
        """
        cls._adapters[cms_type.lower()] = adapter_class
        logger.info("cms_adapter_registered", cms_type=cms_type)

    @classmethod
    def get_supported_cms_types(cls) -> list[str]:
        """Get list of supported CMS types.

        Returns:
            list: List of supported CMS type identifiers
        """
        return list(cls._adapters.keys())


def get_cms_adapter(
    cms_type: str | None = None,
    base_url: str | None = None,
    credentials: dict[str, str] | None = None,
) -> CMSAdapter:
    """Convenience function to get a CMS adapter.

    Args:
        cms_type: CMS platform type (defaults to settings.CMS_TYPE)
        base_url: CMS base URL (defaults to settings.CMS_BASE_URL)
        credentials: Authentication credentials (defaults from settings)

    Returns:
        CMSAdapter: CMS adapter instance

    Example:
        adapter = get_cms_adapter()
        result = await adapter.publish_article(metadata)
    """
    return CMSAdapterFactory.create(cms_type, base_url, credentials)
