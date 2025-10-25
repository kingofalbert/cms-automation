"""CMS adapter services for platform integration."""

from src.services.cms_adapter.base import ArticleMetadata, CMSAdapter, PublishResult
from src.services.cms_adapter.factory import CMSAdapterFactory, get_cms_adapter
from src.services.cms_adapter.wordpress_adapter import WordPressAdapter

__all__ = [
    "CMSAdapter",
    "ArticleMetadata",
    "PublishResult",
    "WordPressAdapter",
    "CMSAdapterFactory",
    "get_cms_adapter",
]
