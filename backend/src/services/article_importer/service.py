"""Article import service - unified entry point for all importers."""

from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_logger
from src.models import Article, SEOMetadata, UploadedFile
from src.services.article_importer.base import ArticleImporter, ImportedArticle, ImportResult
from src.services.article_importer.csv_importer import CSVImporter
from src.services.article_importer.json_importer import JSONImporter
from src.services.article_importer.wordpress_importer import WordPressImporter
from src.services.image_downloader import create_image_downloader

logger = get_logger(__name__)


class ArticleImportService:
    """Service for importing articles from various file formats.

    Supports:
        - CSV files (.csv)
        - JSON files (.json)
        - WordPress exports (.xml, .wxr)

    Usage:
        service = ArticleImportService(db_session)
        result = await service.import_from_file("/path/to/articles.csv")
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize import service.

        Args:
            session: Database session
        """
        self.session = session

    async def import_from_file(
        self,
        file_path: str,
        file_format: Optional[str] = None,
    ) -> ImportResult:
        """Import articles from a file.

        Args:
            file_path: Path to the import file
            file_format: File format (csv, json, wordpress). Auto-detected if None.

        Returns:
            ImportResult with statistics and errors

        Raises:
            ValueError: If file format is unsupported or invalid
            FileNotFoundError: If file doesn't exist
        """
        # Auto-detect format if not specified
        if file_format is None:
            file_format = self._detect_format(file_path)

        # Get appropriate importer
        importer = self._get_importer(file_format)

        logger.info(
            "import_started",
            file_path=file_path,
            format=file_format,
        )

        # Parse file
        try:
            articles = await importer.parse_file(file_path)
        except Exception as e:
            logger.error(
                "import_parse_failed",
                file_path=file_path,
                error=str(e),
                exc_info=True,
            )
            raise

        # Initialize result
        result = ImportResult(
            total_records=len(articles),
            successful_imports=0,
            failed_imports=0,
        )

        # Import each article
        for idx, article in enumerate(articles, start=1):
            try:
                # Validate article
                is_valid, error_msg = await importer.validate_article(article)
                if not is_valid:
                    result.add_error(idx, error_msg or "Validation failed", article.raw_data)
                    continue

                # Save to database
                article_id = await self._save_article(article)
                result.add_success(article_id)

            except Exception as e:
                logger.warning(
                    "article_import_failed",
                    index=idx,
                    title=article.title[:100],
                    error=str(e),
                )
                result.add_error(idx, str(e), article.raw_data)
                continue

        # Commit all successful imports
        try:
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            logger.error(
                "import_commit_failed",
                error=str(e),
                exc_info=True,
            )
            raise

        logger.info(
            "import_completed",
            total=result.total_records,
            successful=result.successful_imports,
            failed=result.failed_imports,
            success_rate=f"{result.success_rate:.1f}%",
        )

        return result

    def _detect_format(self, file_path: str) -> str:
        """Auto-detect file format from extension.

        Args:
            file_path: Path to file

        Returns:
            Format string (csv, json, wordpress)

        Raises:
            ValueError: If format cannot be detected
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        format_map = {
            ".csv": "csv",
            ".json": "json",
            ".xml": "wordpress",
            ".wxr": "wordpress",
        }

        file_format = format_map.get(extension)
        if not file_format:
            raise ValueError(
                f"Unsupported file format: {extension}. "
                f"Supported formats: {list(format_map.keys())}"
            )

        return file_format

    def _get_importer(self, file_format: str) -> ArticleImporter:
        """Get importer instance for format.

        Args:
            file_format: Format string (csv, json, wordpress)

        Returns:
            ArticleImporter instance

        Raises:
            ValueError: If format is unsupported
        """
        importers = {
            "csv": CSVImporter,
            "json": JSONImporter,
            "wordpress": WordPressImporter,
        }

        importer_class = importers.get(file_format.lower())
        if not importer_class:
            raise ValueError(
                f"Unsupported format: {file_format}. "
                f"Supported formats: {list(importers.keys())}"
            )

        return importer_class()

    async def _save_article(self, imported_article: ImportedArticle) -> int:
        """Save imported article to database.

        Args:
            imported_article: Parsed article data

        Returns:
            Article ID

        Raises:
            Exception: If save fails
        """
        # Create Article model
        article = Article(
            title=imported_article.title,
            body=imported_article.body,
            status=imported_article.status,
            author_id=imported_article.author_id,
            source=imported_article.source,
            featured_image_path=imported_article.featured_image_path,
            additional_images=imported_article.additional_images or [],
            cms_article_id=imported_article.cms_article_id,
            published_url=imported_article.published_url,
            published_at=imported_article.published_at,
            article_metadata=imported_article.article_metadata,
            formatting=imported_article.formatting,
        )

        self.session.add(article)
        await self.session.flush()  # Get article.id

        # Process images (download from URLs and upload to Google Drive)
        await self._process_article_images(article, imported_article)

        # Create SEO metadata if present
        if imported_article.seo_metadata:
            try:
                await self._save_seo_metadata(article.id, imported_article.seo_metadata)
            except Exception as e:
                logger.warning(
                    "seo_metadata_save_failed",
                    article_id=article.id,
                    error=str(e),
                )
                # Continue even if SEO save fails (SEO is optional)

        logger.debug(
            "article_saved",
            article_id=article.id,
            title=article.title[:100],
        )

        return article.id

    async def _process_article_images(
        self,
        article: Article,
        imported_article: ImportedArticle,
    ) -> None:
        """Process article images (download from URLs and upload to Google Drive).

        Args:
            article: Article model instance (with ID)
            imported_article: Imported article data

        Note:
            Updates article.featured_image_path and article.additional_images
            with Google Drive file IDs if images were URLs.
        """
        # Only process if Google Drive is configured
        try:
            from src.config import get_settings

            settings = get_settings()
            if not settings.GOOGLE_DRIVE_CREDENTIALS_PATH or not settings.GOOGLE_DRIVE_FOLDER_ID:
                logger.debug(
                    "google_drive_not_configured",
                    article_id=article.id,
                    message="Skipping image upload - Google Drive not configured",
                )
                return
        except Exception:
            # Google Drive not configured, skip image processing
            return

        try:
            downloader = await create_image_downloader()

            # Process featured image
            if imported_article.featured_image_path and self._is_url(imported_article.featured_image_path):
                try:
                    uploaded_file = await downloader.download_and_upload(
                        image_url=imported_article.featured_image_path,
                        article_id=article.id,
                    )
                    self.session.add(uploaded_file)
                    await self.session.flush()

                    # Update article with Drive file ID
                    article.featured_image_path = uploaded_file.drive_file_id

                    logger.info(
                        "featured_image_uploaded",
                        article_id=article.id,
                        drive_file_id=uploaded_file.drive_file_id,
                        original_url=imported_article.featured_image_path,
                    )

                except Exception as e:
                    logger.warning(
                        "featured_image_upload_failed",
                        article_id=article.id,
                        url=imported_article.featured_image_path,
                        error=str(e),
                    )
                    # Keep original URL if upload fails

            # Process additional images
            if imported_article.additional_images:
                processed_images = []
                for img_url in imported_article.additional_images:
                    if self._is_url(img_url):
                        try:
                            uploaded_file = await downloader.download_and_upload(
                                image_url=img_url,
                                article_id=article.id,
                            )
                            self.session.add(uploaded_file)
                            await self.session.flush()

                            # Add Drive file ID to list
                            processed_images.append(uploaded_file.drive_file_id)

                            logger.debug(
                                "additional_image_uploaded",
                                article_id=article.id,
                                drive_file_id=uploaded_file.drive_file_id,
                                original_url=img_url,
                            )

                        except Exception as e:
                            logger.warning(
                                "additional_image_upload_failed",
                                article_id=article.id,
                                url=img_url,
                                error=str(e),
                            )
                            # Keep original URL if upload fails
                            processed_images.append(img_url)
                    else:
                        # Not a URL, keep as-is
                        processed_images.append(img_url)

                # Update article with processed images
                article.additional_images = processed_images

            await downloader.close()

        except Exception as e:
            logger.error(
                "image_processing_failed",
                article_id=article.id,
                error=str(e),
                exc_info=True,
            )
            # Don't fail the import if image processing fails

    def _is_url(self, path: str) -> bool:
        """Check if a string is a URL.

        Args:
            path: Path or URL string

        Returns:
            True if string is a URL, False otherwise
        """
        if not path:
            return False

        return path.startswith(("http://", "https://", "ftp://"))

    async def _save_seo_metadata(self, article_id: int, seo_data: dict) -> None:
        """Save SEO metadata for article.

        Args:
            article_id: Article ID
            seo_data: SEO metadata dictionary

        Raises:
            Exception: If save fails
        """
        # Only create if we have required fields
        if not seo_data.get("meta_title") or not seo_data.get("meta_description"):
            logger.debug(
                "seo_metadata_skipped",
                article_id=article_id,
                reason="Missing required fields (meta_title, meta_description)",
            )
            return

        # Validate field presence
        if not seo_data.get("focus_keyword"):
            logger.debug(
                "seo_metadata_skipped",
                article_id=article_id,
                reason="Missing focus_keyword",
            )
            return

        seo_metadata = SEOMetadata(
            article_id=article_id,
            meta_title=seo_data["meta_title"],
            meta_description=seo_data["meta_description"],
            focus_keyword=seo_data["focus_keyword"],
            primary_keywords=seo_data.get("primary_keywords"),
            secondary_keywords=seo_data.get("secondary_keywords"),
            readability_score=seo_data.get("readability_score"),
            seo_score=seo_data.get("seo_score"),
        )

        self.session.add(seo_metadata)

        logger.debug(
            "seo_metadata_saved",
            article_id=article_id,
            focus_keyword=seo_data["focus_keyword"],
        )
