"""Article processing orchestrator for Phase 7.

This service orchestrates the complete article processing pipeline:
1. Parse article HTML (AI or heuristic)
2. Download and process images
3. Extract image metadata
4. Save to database
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.article import Article
from src.models.article_image import ArticleImage
from src.services.parser.article_parser import ArticleParserService
from src.services.parser.image_processor import ImageProcessorService
from src.services.parser.models import ParsedArticle, ParsingResult

logger = logging.getLogger(__name__)


class ArticleProcessingService:
    """Service for processing articles with images and metadata extraction."""

    def __init__(
        self,
        article_parser: ArticleParserService,
        image_processor: ImageProcessorService,
        storage_base_path: str = "/tmp/cms_images",
    ):
        """Initialize article processing service.

        Args:
            article_parser: ArticleParserService instance
            image_processor: ImageProcessorService instance
            storage_base_path: Base path for storing downloaded images
        """
        self.article_parser = article_parser
        self.image_processor = image_processor
        self.storage_base_path = Path(storage_base_path)
        self.storage_base_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"ArticleProcessingService initialized (storage_path={storage_base_path})"
        )

    async def process_article(
        self,
        article_id: int,
        raw_html: str,
        db_session: AsyncSession,
        download_images: bool = True,
    ) -> dict[str, Any]:
        """Process article HTML and extract structured data with images.

        Args:
            article_id: Database ID of the article
            raw_html: Raw HTML from Google Docs
            db_session: Database session for saving data
            download_images: Whether to download and process images

        Returns:
            Processing result with status and metadata
        """
        logger.info(f"Processing article {article_id}")
        start_time = datetime.utcnow()

        # Step 1: Parse article HTML
        parsing_result = self.article_parser.parse_document(raw_html)

        if not parsing_result.success:
            logger.error(f"Article parsing failed: {parsing_result.errors}")
            return {
                "success": False,
                "errors": [e.error_message for e in parsing_result.errors],
                "duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
            }

        parsed_article = parsing_result.parsed_article
        logger.info(
            f"Article parsed successfully: {parsed_article.title_main}, "
            f"{len(parsed_article.images)} images"
        )

        # Step 2: Update article record with parsed data
        article = await self._update_article_record(
            article_id, parsed_article, db_session
        )

        # Step 3: Process images if requested
        processed_images = []
        if download_images and parsed_article.images:
            processed_images = await self._process_images(
                article_id, parsed_article.images, db_session
            )

        # Step 4: Commit transaction
        await db_session.commit()

        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        logger.info(
            f"Article {article_id} processed successfully in {duration_ms:.0f}ms: "
            f"{len(processed_images)} images processed"
        )

        return {
            "success": True,
            "article_id": article_id,
            "parsing_method": parsed_article.parsing_method,
            "parsing_confidence": parsed_article.parsing_confidence,
            "images_processed": len(processed_images),
            "duration_ms": duration_ms,
            "warnings": parsing_result.warnings,
        }

    async def _update_article_record(
        self,
        article_id: int,
        parsed_article: ParsedArticle,
        db_session: AsyncSession,
    ) -> Article:
        """Update article database record with parsed data.

        Args:
            article_id: Database ID of the article
            parsed_article: Parsed article data
            db_session: Database session

        Returns:
            Updated Article model
        """
        # Fetch article from database
        article = await db_session.get(Article, article_id)
        if not article:
            raise ValueError(f"Article {article_id} not found in database")

        # Update fields from parsed data
        article.title_prefix = parsed_article.title_prefix
        article.title_main = parsed_article.title_main
        article.title_suffix = parsed_article.title_suffix
        article.author_line = parsed_article.author_line
        article.author_name = parsed_article.author_name
        article.body_html = parsed_article.body_html
        article.meta_description = parsed_article.meta_description
        article.seo_keywords = parsed_article.seo_keywords

        # Note: parsing_confirmed remains False until user confirms
        # parsing_confirmed_at and parsing_confirmed_by will be set by API endpoint

        logger.debug(f"Updated article {article_id} with parsed data")
        return article

    async def _process_images(
        self,
        article_id: int,
        parsed_images: list,
        db_session: AsyncSession,
    ) -> list[ArticleImage]:
        """Download and process images for an article.

        Args:
            article_id: Database ID of the article
            parsed_images: List of ParsedImage objects from parser
            db_session: Database session

        Returns:
            List of created ArticleImage database records
        """
        logger.info(f"Processing {len(parsed_images)} images for article {article_id}")

        created_images = []

        for idx, parsed_img in enumerate(parsed_images):
            try:
                # Download image
                logger.debug(
                    f"Downloading image {idx+1}/{len(parsed_images)}: {parsed_img.source_url}"
                )

                # Generate storage paths
                article_dir = self.storage_base_path / f"article_{article_id}"
                article_dir.mkdir(parents=True, exist_ok=True)

                source_filename = f"image_{idx}_{Path(parsed_img.source_url).suffix or '.jpg'}"
                source_path = article_dir / source_filename
                preview_path = article_dir / f"preview_{source_filename}"

                # Download and extract metadata
                image_metadata = await self.image_processor.process_image_from_url(
                    parsed_img.source_url,
                    download_to_path=str(source_path),
                )

                # TODO: Generate preview/thumbnail (future enhancement)
                # For now, just use same image for preview
                preview_path = source_path

                # Create database record
                article_image = ArticleImage(
                    article_id=article_id,
                    preview_path=str(preview_path),
                    source_path=str(source_path),
                    source_url=parsed_img.source_url,
                    caption=parsed_img.caption,
                    position=parsed_img.position,
                    image_metadata=image_metadata,
                )

                db_session.add(article_image)
                created_images.append(article_image)

                logger.debug(
                    f"Image {idx+1} processed: {article_image.image_width}x{article_image.image_height}px"
                )

            except Exception as e:
                logger.error(
                    f"Failed to process image {idx+1} ({parsed_img.source_url}): {e}"
                )
                # Continue processing other images
                continue

        logger.info(
            f"Successfully processed {len(created_images)}/{len(parsed_images)} images"
        )
        return created_images

    async def reprocess_images(
        self,
        article_id: int,
        db_session: AsyncSession,
    ) -> dict[str, Any]:
        """Reprocess images for an existing article.

        Useful for regenerating metadata or re-downloading images.

        Args:
            article_id: Database ID of the article
            db_session: Database session

        Returns:
            Processing result
        """
        logger.info(f"Reprocessing images for article {article_id}")

        # Fetch article
        article = await db_session.get(Article, article_id)
        if not article:
            raise ValueError(f"Article {article_id} not found")

        # Delete existing images
        for img in article.article_images:
            await db_session.delete(img)

        # Re-parse to get image URLs
        if not article.raw_html:
            raise ValueError(f"Article {article_id} has no raw_html to reprocess")

        parsing_result = self.article_parser.parse_document(article.raw_html)
        if not parsing_result.success:
            return {"success": False, "errors": parsing_result.errors}

        # Process images
        processed_images = await self._process_images(
            article_id, parsing_result.parsed_article.images, db_session
        )

        await db_session.commit()

        logger.info(f"Reprocessed {len(processed_images)} images for article {article_id}")
        return {
            "success": True,
            "images_reprocessed": len(processed_images),
        }

    async def close(self) -> None:
        """Close resources (HTTP clients, etc.)."""
        await self.image_processor.close()


async def create_article_processor(
    use_ai_parsing: bool = True,
    anthropic_api_key: str | None = None,
    storage_path: str = "/tmp/cms_images",
) -> ArticleProcessingService:
    """Factory function to create ArticleProcessingService.

    Args:
        use_ai_parsing: Whether to use AI-based parsing
        anthropic_api_key: Anthropic API key (required if use_ai_parsing=True)
        storage_path: Base path for image storage

    Returns:
        ArticleProcessingService instance
    """
    article_parser = ArticleParserService(
        use_ai=use_ai_parsing,
        anthropic_api_key=anthropic_api_key,
    )

    image_processor = ImageProcessorService()

    return ArticleProcessingService(
        article_parser=article_parser,
        image_processor=image_processor,
        storage_base_path=storage_path,
    )
