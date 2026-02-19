"""Article processing orchestrator for Phase 7.

This service orchestrates the complete article processing pipeline:
1. Parse article HTML (AI or heuristic)
2. Download and process images
3. Extract image metadata
4. Match related articles for internal linking (Phase 12)
5. Save to database
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.article import Article
from src.models.article_faq import ArticleFAQ
from src.models.article_image import ArticleImage
from src.services.internal_links import InternalLinkService, get_internal_link_service
from src.services.parser.article_parser import ArticleParserService
from src.services.parser.image_processor import ImageProcessorService
from src.services.parser.models import ParsedArticle, ParsingResult, RelatedArticle

logger = logging.getLogger(__name__)


class ArticleProcessingService:
    """Service for processing articles with images and metadata extraction."""

    def __init__(
        self,
        article_parser: ArticleParserService,
        image_processor: ImageProcessorService,
        storage_base_path: str = "/tmp/cms_images",
        internal_link_service: InternalLinkService | None = None,
    ):
        """Initialize article processing service.

        Args:
            article_parser: ArticleParserService instance
            image_processor: ImageProcessorService instance
            storage_base_path: Base path for storing downloaded images
            internal_link_service: InternalLinkService for related article matching
        """
        self.article_parser = article_parser
        self.image_processor = image_processor
        self.storage_base_path = Path(storage_base_path)
        self.storage_base_path.mkdir(parents=True, exist_ok=True)
        self.internal_link_service = internal_link_service or get_internal_link_service()

        logger.info(
            f"ArticleProcessingService initialized (storage_path={storage_base_path}, "
            f"internal_links_enabled={self.internal_link_service.is_configured})"
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

        # Step 3.5: Apply document image alt texts to processed images (Phase 15)
        if parsed_article.doc_image_alt_texts and processed_images:
            await self._apply_doc_image_alt_texts(
                processed_images, parsed_article.doc_image_alt_texts, db_session
            )

        # Step 4: Match related articles for internal linking (Phase 12)
        related_articles_count = 0
        if self.internal_link_service.is_configured:
            related_articles = await self._match_related_articles(parsed_article)
            parsed_article.related_articles = related_articles
            related_articles_count = len(related_articles)

            # Save related articles to database
            if related_articles:
                await self._save_related_articles(
                    article_id, related_articles, db_session
                )

        # Step 5: Commit transaction
        await db_session.commit()

        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        logger.info(
            f"Article {article_id} processed successfully in {duration_ms:.0f}ms: "
            f"{len(processed_images)} images, {related_articles_count} related articles"
        )

        return {
            "success": True,
            "article_id": article_id,
            "parsing_method": parsed_article.parsing_method,
            "parsing_confidence": parsed_article.parsing_confidence,
            "images_processed": len(processed_images),
            "related_articles_count": related_articles_count,
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

        # Store parsing metadata
        article.parsing_method = parsed_article.parsing_method
        article.parsing_confidence = parsed_article.parsing_confidence

        # Store taxonomy fields (tags, categories)
        if parsed_article.tags:
            article.tags = parsed_article.tags
        if parsed_article.primary_category:
            article.primary_category = parsed_article.primary_category
        if parsed_article.secondary_categories:
            article.secondary_categories = parsed_article.secondary_categories

        # Store SEO fields
        if parsed_article.focus_keyword:
            article.focus_keyword = parsed_article.focus_keyword
        if parsed_article.seo_title:
            article.seo_title = parsed_article.seo_title
            article.seo_title_extracted = parsed_article.seo_title_extracted
            article.seo_title_source = parsed_article.seo_title_source

        # Store AI suggestions for user review
        if parsed_article.suggested_titles:
            article.suggested_titles = parsed_article.suggested_titles
        if parsed_article.suggested_meta_description:
            article.suggested_meta_description = parsed_article.suggested_meta_description
        if parsed_article.suggested_seo_keywords:
            article.suggested_seo_keywords = parsed_article.suggested_seo_keywords

        # Store proofreading issues if available
        if parsed_article.proofreading_issues:
            article.proofreading_issues = parsed_article.proofreading_issues

        # Note: parsing_confirmed remains False until user confirms
        # parsing_confirmed_at and parsing_confirmed_by will be set by API endpoint

        # Phase 14: Store extracted FAQs (from original article HTML)
        if parsed_article.extracted_faqs:
            article.extracted_faqs = parsed_article.extracted_faqs
            article.extracted_faqs_detection_method = parsed_article.extracted_faqs_detection_method
            logger.debug(
                f"Stored {len(parsed_article.extracted_faqs)} extracted FAQs "
                f"(method: {parsed_article.extracted_faqs_detection_method})"
            )

        # Phase 15: Store document metadata sections (AEO, SEO variants, proofreading, alt texts)
        if parsed_article.aeo_type:
            article.aeo_type = parsed_article.aeo_type
        if parsed_article.aeo_paragraph:
            article.aeo_paragraph = parsed_article.aeo_paragraph
        if parsed_article.seo_title_variants:
            article.seo_title_variants = parsed_article.seo_title_variants
        if parsed_article.doc_proofreading_suggestions:
            article.doc_proofreading_suggestions = parsed_article.doc_proofreading_suggestions
            logger.debug(
                f"Stored {len(parsed_article.doc_proofreading_suggestions)} "
                f"proofreading suggestions from document"
            )
        if parsed_article.doc_image_alt_texts:
            article.doc_image_alt_texts = parsed_article.doc_image_alt_texts
            logger.debug(
                f"Stored {len(parsed_article.doc_image_alt_texts)} "
                f"image alt texts from document"
            )

        logger.debug(f"Updated article {article_id} with parsed data (including tags, categories, SEO, AEO fields)")

        # Phase 7.5: Save AI-generated FAQs to article_faqs table
        # This allows FAQs to be displayed immediately without needing manual generation
        if parsed_article.faqs:
            await self._save_faqs_to_database(article_id, parsed_article.faqs, db_session)

        return article

    async def _match_related_articles(
        self,
        parsed_article: ParsedArticle,
    ) -> list[RelatedArticle]:
        """Match related articles for internal linking (Phase 12).

        Args:
            parsed_article: Parsed article data with title and keywords

        Returns:
            List of related article matches
        """
        logger.info(f"Matching related articles for: {parsed_article.title_main[:50]}...")

        try:
            result = await self.internal_link_service.match_related_articles(
                title=parsed_article.title_main,
                keywords=parsed_article.seo_keywords or [],
                limit=5,
            )

            if not result.success:
                logger.warning(f"Related article matching failed: {result.error}")
                return []

            # Convert to RelatedArticle models
            related_articles = []
            for match in result.matches:
                related_article = RelatedArticle(
                    article_id=match.article_id,
                    title=match.title,
                    title_main=match.title_main,
                    url=match.url,
                    excerpt=match.excerpt,
                    similarity=match.similarity,
                    match_type=match.match_type,
                    ai_keywords=match.ai_keywords,
                )
                related_articles.append(related_article)

            logger.info(f"Found {len(related_articles)} related articles")
            return related_articles

        except Exception as e:
            logger.error(f"Error matching related articles: {e}")
            return []

    async def _save_related_articles(
        self,
        article_id: int,
        related_articles: list[RelatedArticle],
        db_session: AsyncSession,
    ) -> None:
        """Save related articles to the article record.

        Args:
            article_id: Database ID of the article
            related_articles: List of related articles to save
            db_session: Database session
        """
        article = await db_session.get(Article, article_id)
        if not article:
            logger.warning(f"Article {article_id} not found, skipping related articles save")
            return

        # Convert to serializable format
        article.related_articles = [
            {
                "article_id": ra.article_id,
                "title": ra.title,
                "title_main": ra.title_main,
                "url": ra.url,
                "excerpt": ra.excerpt,
                "similarity": ra.similarity,
                "match_type": ra.match_type,
                "ai_keywords": ra.ai_keywords,
            }
            for ra in related_articles
        ]

        logger.info(f"Saved {len(related_articles)} related articles for article {article_id}")

    async def _save_faqs_to_database(
        self,
        article_id: int,
        faqs: list[dict],
        db_session: AsyncSession,
    ) -> None:
        """Save AI-generated FAQs from parsing to database.

        Args:
            article_id: Database ID of the article
            faqs: List of FAQ dictionaries from parsed article
            db_session: Database session
        """
        from sqlalchemy import delete

        logger.info(f"Saving {len(faqs)} FAQs for article {article_id}")

        # Delete existing FAQs for this article (if re-parsing)
        stmt = delete(ArticleFAQ).where(ArticleFAQ.article_id == article_id)
        await db_session.execute(stmt)

        # Create new FAQ records
        for position, faq_data in enumerate(faqs):
            # Validate question_type
            question_type = faq_data.get("question_type", "factual")
            if question_type not in ("factual", "how_to", "comparison", "definition"):
                question_type = "factual"

            # Validate search_intent
            search_intent = faq_data.get("search_intent", "informational")
            if search_intent not in ("informational", "navigational", "transactional"):
                search_intent = "informational"

            # Get intent field (some prompts use 'intent' instead of 'search_intent')
            if not faq_data.get("search_intent") and faq_data.get("intent"):
                intent = faq_data.get("intent", "informational")
                if intent in ("informational", "navigational", "transactional"):
                    search_intent = intent

            faq = ArticleFAQ(
                article_id=article_id,
                question=faq_data.get("question", ""),
                answer=faq_data.get("answer", ""),
                question_type=question_type,
                search_intent=search_intent,
                keywords_covered=faq_data.get("keywords_covered", []),
                confidence=faq_data.get("confidence"),
                position=position,
                status="draft",  # Default status for AI-generated FAQs
            )
            db_session.add(faq)

        logger.info(f"Successfully saved {len(faqs)} FAQs for article {article_id}")

    async def _apply_doc_image_alt_texts(
        self,
        article_images: list[ArticleImage],
        doc_alt_texts: list[dict],
        db_session: AsyncSession,
    ) -> None:
        """Apply human-written alt texts from document to ArticleImage records.

        Matches by position (1-based in doc → 0-based in images).
        Also stores the Google Drive link for reference.

        Args:
            article_images: List of ArticleImage records from image processing
            doc_alt_texts: List of {position, alt_text, drive_link} from document
            db_session: Database session
        """
        if not doc_alt_texts:
            return

        # Build lookup by position (doc uses 1-based indexing)
        alt_text_map: dict[int, dict] = {}
        for item in doc_alt_texts:
            pos = item.get("position", 0)
            alt_text_map[pos] = item

        applied_count = 0
        for img in article_images:
            # Try 1-based position matching (doc position 1 = image index 0)
            doc_pos = img.position + 1
            if doc_pos in alt_text_map:
                alt_data = alt_text_map[doc_pos]
                if alt_data.get("alt_text"):
                    img.alt_text = alt_data["alt_text"]
                    applied_count += 1
                    logger.debug(
                        f"Applied doc alt text to image at position {img.position}: "
                        f"'{alt_data['alt_text'][:50]}...'"
                    )

        if applied_count:
            logger.info(
                f"[P15] Applied {applied_count}/{len(article_images)} "
                f"image alt texts from document"
            )

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
