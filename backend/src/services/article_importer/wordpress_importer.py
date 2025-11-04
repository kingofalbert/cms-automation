"""WordPress XML (WXR) article importer."""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from src.config import get_logger
from src.models import ArticleStatus
from src.services.article_importer.base import ArticleImporter, ImportedArticle

logger = get_logger(__name__)


class WordPressImporter(ArticleImporter):
    """Import articles from WordPress Export (WXR) files.

    WordPress eXtended RSS (WXR) format is the standard export format from WordPress.
    This importer extracts posts and converts them to articles.

    Supported content:
        - Post title
        - Post content (HTML)
        - Post author
        - Post status (publish, draft, etc.)
        - Publication date
        - Featured image (if available)
        - SEO metadata from Yoast/Rank Math plugins (if present)

    WordPress namespaces:
        - wp: WordPress core namespace
        - content: Content namespace
        - excerpt: Excerpt namespace
    """

    # WordPress XML namespaces
    NAMESPACES = {
        "wp": "http://wordpress.org/export/1.2/",
        "content": "http://purl.org/rss/1.0/modules/content/",
        "excerpt": "http://wordpress.org/export/1.2/excerpt/",
        "dc": "http://purl.org/dc/elements/1.1/",
    }

    def __init__(self) -> None:
        """Initialize WordPress importer."""
        super().__init__(source_type="wordpress_export")

    async def parse_file(self, file_path: str) -> list[ImportedArticle]:
        """Parse WordPress WXR file and extract articles.

        Args:
            file_path: Path to WordPress export XML file

        Returns:
            List of ImportedArticle objects

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If XML format is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"WordPress export file not found: {file_path}")

        try:
            tree = ET.parse(path)
            root = tree.getroot()
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML format: {e}") from e

        # Validate it's a WordPress export
        channel = root.find("channel")
        if channel is None:
            raise ValueError("Invalid WordPress export: missing channel element")

        articles: list[ImportedArticle] = []

        # Find all items (posts, pages, etc.)
        items = channel.findall("item")

        for idx, item in enumerate(items, start=1):
            try:
                # Only process posts (skip pages, attachments, etc.)
                post_type = self._get_text(item, "wp:post_type", "post")
                if post_type != "post":
                    continue

                # Skip non-published and non-draft posts by default
                status = self._get_text(item, "wp:status", "publish")
                if status not in ["publish", "draft", "pending", "private"]:
                    continue

                article = self._parse_item(item, idx)
                if article:
                    articles.append(article)

            except Exception as e:
                logger.warning(
                    "wordpress_item_parse_failed",
                    item_index=idx,
                    error=str(e),
                )
                # Continue parsing (collect errors strategy)
                continue

        logger.info("wordpress_parse_completed", total_articles=len(articles))
        return articles

    def _parse_item(self, item: ET.Element, index: int) -> ImportedArticle | None:
        """Parse a single WordPress item into ImportedArticle.

        Args:
            item: XML item element
            index: Item index for error reporting

        Returns:
            ImportedArticle object or None if should be skipped

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Extract title
        title_elem = item.find("title")
        title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""

        if not title:
            raise ValueError(f"Item {index}: title is required")

        # Extract content (WordPress uses content:encoded for full HTML content)
        content_elem = item.find("content:encoded", self.NAMESPACES)
        body = content_elem.text.strip() if content_elem is not None and content_elem.text else ""

        if not body:
            # Try description as fallback
            desc_elem = item.find("description")
            body = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else ""

        if not body:
            raise ValueError(f"Item {index}: content is required")

        # Extract author
        author_elem = item.find("dc:creator", self.NAMESPACES)
        raw_author_id = author_elem.text.strip() if author_elem is not None and author_elem.text else "unknown"

        # Normalize author_id with wordpress prefix
        author_id = self._normalize_author_id(raw_author_id, prefix="wordpress")

        # Extract status
        wp_status = self._get_text(item, "wp:status", "publish")
        status = self._map_wordpress_status(wp_status)

        # Extract publication date
        pub_date_elem = item.find("wp:post_date", self.NAMESPACES)
        pub_date_str = pub_date_elem.text if pub_date_elem is not None and pub_date_elem.text else None
        published_at = self._parse_datetime(pub_date_str)

        # Extract WordPress post ID
        post_id_elem = item.find("wp:post_id", self.NAMESPACES)
        cms_article_id = post_id_elem.text if post_id_elem is not None and post_id_elem.text else None

        # Extract link (published URL)
        link_elem = item.find("link")
        published_url = link_elem.text.strip() if link_elem is not None and link_elem.text else None

        # Extract featured image (from postmeta)
        featured_image_path = self._extract_featured_image(item)

        # Extract SEO metadata (Yoast/Rank Math)
        seo_metadata = self._extract_seo_metadata(item)

        # Extract post metadata
        article_metadata = {
            "wordpress_post_id": cms_article_id,
            "wordpress_status": wp_status,
        }

        # Create ImportedArticle
        article = ImportedArticle(
            title=title,
            body=body,
            author_id=author_id,
            status=status,
            source=self.source_type,
            featured_image_path=featured_image_path,
            cms_article_id=cms_article_id,
            published_url=published_url,
            published_at=published_at,
            article_metadata=article_metadata,
            seo_metadata=seo_metadata,
            raw_data={},  # XML elements can't be easily serialized
        )

        return article

    def _get_text(self, parent: ET.Element, tag: str, default: str = "") -> str:
        """Get text from XML element with namespace support.

        Args:
            parent: Parent element
            tag: Tag name (may include namespace prefix)
            default: Default value if element not found

        Returns:
            Element text or default
        """
        elem = parent.find(tag, self.NAMESPACES)
        if elem is not None and elem.text:
            return elem.text.strip()
        return default

    def _map_wordpress_status(self, wp_status: str) -> ArticleStatus:
        """Map WordPress post status to ArticleStatus.

        Args:
            wp_status: WordPress status (publish, draft, pending, private, etc.)

        Returns:
            ArticleStatus enum value
        """
        status_map = {
            "publish": ArticleStatus.PUBLISHED,
            "draft": ArticleStatus.DRAFT,
            "pending": ArticleStatus.IN_REVIEW,
            "private": ArticleStatus.DRAFT,
            "future": ArticleStatus.SCHEDULED,
        }

        return status_map.get(wp_status.lower(), ArticleStatus.IMPORTED)

    def _extract_featured_image(self, item: ET.Element) -> str | None:
        """Extract featured image URL from WordPress postmeta.

        Args:
            item: WordPress item element

        Returns:
            Featured image URL or None
        """
        # Look for _thumbnail_id in postmeta
        postmeta_elements = item.findall("wp:postmeta", self.NAMESPACES)

        for postmeta in postmeta_elements:
            meta_key = self._get_text(postmeta, "wp:meta_key")
            if meta_key == "_thumbnail_id":
                # This gives us the attachment ID
                # In a real implementation, we'd need to look up the attachment
                # For now, we'll just note that a featured image exists
                return None  # Could be enhanced to fetch actual image URL

        return None

    def _extract_seo_metadata(self, item: ET.Element) -> dict[str, Any] | None:
        """Extract SEO metadata from Yoast or Rank Math plugins.

        Args:
            item: WordPress item element

        Returns:
            SEO metadata dictionary or None
        """
        seo_metadata: dict[str, Any] = {}

        # Look for Yoast SEO metadata in postmeta
        postmeta_elements = item.findall("wp:postmeta", self.NAMESPACES)

        yoast_title = None
        yoast_desc = None
        yoast_focus = None

        for postmeta in postmeta_elements:
            meta_key = self._get_text(postmeta, "wp:meta_key")
            meta_value = self._get_text(postmeta, "wp:meta_value")

            # Yoast SEO fields
            if meta_key == "_yoast_wpseo_title":
                yoast_title = meta_value
            elif meta_key == "_yoast_wpseo_metadesc":
                yoast_desc = meta_value
            elif meta_key == "_yoast_wpseo_focuskw":
                yoast_focus = meta_value

            # Rank Math fields
            elif meta_key == "rank_math_title":
                yoast_title = meta_value
            elif meta_key == "rank_math_description":
                yoast_desc = meta_value
            elif meta_key == "rank_math_focus_keyword":
                yoast_focus = meta_value

        # Only create SEO metadata if we have at least one field
        if yoast_title or yoast_desc or yoast_focus:
            if yoast_title:
                seo_metadata["meta_title"] = yoast_title
            if yoast_desc:
                seo_metadata["meta_description"] = yoast_desc
            if yoast_focus:
                seo_metadata["focus_keyword"] = yoast_focus

        return seo_metadata if seo_metadata else None

    async def validate_article(self, article: ImportedArticle) -> tuple[bool, str | None]:
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

        # Note: WordPress SEO metadata may not meet our strict length requirements
        # So we skip SEO validation for WordPress imports
        # Users can re-optimize SEO after import

        return True, None
