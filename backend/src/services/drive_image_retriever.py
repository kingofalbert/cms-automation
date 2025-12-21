"""Service for retrieving images from Google Drive for publishing."""

import tempfile
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import get_logger
from src.models.article_image import ArticleImage
from src.models.uploaded_file import UploadedFile
from src.services.storage import create_google_drive_storage

logger = get_logger(__name__)


class DriveImageRetriever:
    """Retrieve images from Google Drive for WordPress publishing.

    This service:
    1. Queries uploaded_files table for images associated with an article
    2. Downloads images from Google Drive to local temp directory
    3. Provides file paths for Computer Use to upload to WordPress
    4. Cleans up temp files after publishing
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize Drive image retriever.

        Args:
            session: Database session for querying uploaded_files
        """
        self.session = session
        self.temp_dir: Path | None = None
        self.downloaded_files: list[dict] = []

    async def get_article_images(self, article_id: int) -> list[dict]:
        """Get all images associated with an article for WordPress publishing.

        This method retrieves images from the article_images table (parsed images)
        which contains position, caption, and alt_text information required for
        proper WordPress publishing.

        Args:
            article_id: Article ID to fetch images for

        Returns:
            List of image metadata dicts with local file paths and publishing metadata

        Example return:
        [
            {
                "filename": "image1.jpg",
                "position": 0,              # Paragraph index for insertion
                "caption": "圖說文字...",    # Image caption from document
                "alt_text": "替代文字...",   # Alt text for SEO/accessibility
                "local_path": "/tmp/images/image1.jpg",
                "source_url": "https://...", # Original source URL
                "mime_type": "image/jpeg",
            }
        ]
        """
        logger.info("retrieving_article_images", article_id=article_id)

        # First, query article_images table for parsed image info (position, caption, alt_text)
        stmt = select(ArticleImage).where(
            ArticleImage.article_id == article_id
        ).order_by(ArticleImage.position)
        result = await self.session.execute(stmt)
        article_images = result.scalars().all()

        if not article_images:
            logger.info("no_parsed_images_found_for_article", article_id=article_id)
            # Fallback: try uploaded_files table for backward compatibility
            return await self._get_images_from_uploaded_files(article_id)

        logger.info(
            "found_parsed_article_images",
            article_id=article_id,
            count=len(article_images),
        )

        # Create temp directory for downloads
        self.temp_dir = Path(tempfile.mkdtemp(prefix="cms_images_"))
        logger.debug("created_temp_directory", path=str(self.temp_dir))

        images = []
        storage = None

        for idx, article_image in enumerate(article_images):
            try:
                local_path = None
                filename = f"image_{idx + 1}"

                # Try to get the image file
                # Priority 1: Use source_path if file exists locally
                if article_image.source_path:
                    source_file = Path(article_image.source_path)
                    if source_file.exists():
                        # Copy to temp directory
                        filename = source_file.name
                        local_path = self.temp_dir / filename
                        local_path.write_bytes(source_file.read_bytes())
                        logger.debug(
                            "image_copied_from_source_path",
                            source_path=str(source_file),
                            local_path=str(local_path),
                        )

                # Priority 2: Download from source_url
                if not local_path and article_image.source_url:
                    try:
                        import httpx
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            response = await client.get(article_image.source_url, follow_redirects=True)
                            if response.status_code == 200:
                                # Extract filename from URL or use index
                                url_path = article_image.source_url.split('?')[0]
                                if '/' in url_path:
                                    filename = url_path.split('/')[-1] or f"image_{idx + 1}.jpg"
                                local_path = self.temp_dir / filename
                                local_path.write_bytes(response.content)
                                logger.debug(
                                    "image_downloaded_from_source_url",
                                    source_url=article_image.source_url[:100],
                                    local_path=str(local_path),
                                )
                    except Exception as download_err:
                        logger.warning(
                            "failed_to_download_from_source_url",
                            source_url=article_image.source_url[:100] if article_image.source_url else None,
                            error=str(download_err),
                        )

                # Priority 3: Try to find in uploaded_files and download from Google Drive
                if not local_path:
                    uploaded_file = await self._find_matching_uploaded_file(article_id, article_image)
                    if uploaded_file:
                        if storage is None:
                            storage = await create_google_drive_storage()
                        try:
                            file_data = await storage.download_file(uploaded_file.drive_file_id)
                            filename = uploaded_file.filename
                            local_path = self.temp_dir / filename
                            local_path.write_bytes(file_data)
                            logger.debug(
                                "image_downloaded_from_drive",
                                drive_file_id=uploaded_file.drive_file_id,
                                local_path=str(local_path),
                            )
                        except Exception as drive_err:
                            logger.warning(
                                "failed_to_download_from_drive",
                                drive_file_id=uploaded_file.drive_file_id,
                                error=str(drive_err),
                            )

                if not local_path:
                    logger.warning(
                        "could_not_retrieve_image_file",
                        article_image_id=article_image.id,
                        position=article_image.position,
                    )
                    continue

                # Build complete image metadata for Computer Use
                # Include all fields needed for proper WordPress publishing
                image_metadata = {
                    # Basic file info
                    "filename": filename,
                    "local_path": str(local_path),
                    "source_url": article_image.source_url or "",
                    "mime_type": self._guess_mime_type(filename),

                    # Position and type classification
                    "position": article_image.position,
                    "is_featured": article_image.is_featured,  # 置頂圖片標記
                    "image_type": article_image.image_type,    # featured/content/inline
                    "detection_method": article_image.detection_method or "",  # 檢測方式

                    # Text content for SEO/accessibility
                    "caption": article_image.caption or "",
                    "alt_text": article_image.alt_text or article_image.caption or "",
                    "description": article_image.description or "",

                    # Technical metadata (dimensions, format, etc.)
                    "image_width": article_image.image_width,
                    "image_height": article_image.image_height,
                    "file_size_bytes": article_image.file_size_bytes,
                    "image_format": article_image.image_format,
                }

                images.append(image_metadata)
                self.downloaded_files.append(image_metadata)

                logger.debug(
                    "image_prepared_for_upload",
                    filename=filename,
                    position=article_image.position,
                    is_featured=article_image.is_featured,
                    image_type=article_image.image_type,
                    detection_method=article_image.detection_method,
                    has_caption=bool(article_image.caption),
                    has_alt_text=bool(article_image.alt_text),
                    has_description=bool(article_image.description),
                )

            except Exception as e:
                logger.error(
                    "failed_to_process_article_image",
                    article_image_id=article_image.id,
                    position=article_image.position,
                    error=str(e),
                    exc_info=True,
                )
                continue

        logger.info(
            "article_images_retrieved",
            article_id=article_id,
            total=len(article_images),
            prepared=len(images),
        )

        return images

    async def _get_images_from_uploaded_files(self, article_id: int) -> list[dict]:
        """Fallback: Get images from uploaded_files table (legacy support).

        This is used when article_images table has no entries, for backward
        compatibility with older articles that only have uploaded_files records.
        """
        logger.info("fallback_to_uploaded_files", article_id=article_id)

        stmt = select(UploadedFile).where(
            UploadedFile.article_id == article_id,
            UploadedFile.file_type == "image",
        )
        result = await self.session.execute(stmt)
        uploaded_files = result.scalars().all()

        if not uploaded_files:
            logger.info("no_uploaded_files_found", article_id=article_id)
            return []

        # Create temp directory for downloads
        self.temp_dir = Path(tempfile.mkdtemp(prefix="cms_images_"))
        storage = await create_google_drive_storage()
        images = []

        for idx, uploaded_file in enumerate(uploaded_files):
            try:
                file_data = await storage.download_file(uploaded_file.drive_file_id)
                local_path = self.temp_dir / uploaded_file.filename
                local_path.write_bytes(file_data)

                # Note: uploaded_files doesn't have position/caption/alt_text
                # Use index as position and empty strings for text fields
                # First image (idx=0) is assumed to be featured for legacy compatibility
                image_metadata = {
                    # Basic file info
                    "filename": uploaded_file.filename,
                    "local_path": str(local_path),
                    "source_url": uploaded_file.web_view_link or "",
                    "mime_type": uploaded_file.mime_type or self._guess_mime_type(uploaded_file.filename),

                    # Position and type classification (fallback defaults)
                    "position": idx,  # Use index as fallback position
                    "is_featured": idx == 0,  # First image assumed featured
                    "image_type": "featured" if idx == 0 else "content",
                    "detection_method": "legacy_fallback",

                    # Text content (not available in uploaded_files)
                    "caption": "",
                    "alt_text": "",
                    "description": "",

                    # Technical metadata (not available)
                    "image_width": None,
                    "image_height": None,
                    "file_size_bytes": None,
                    "image_format": None,
                }

                images.append(image_metadata)
                self.downloaded_files.append(image_metadata)

            except Exception as e:
                logger.error(
                    "failed_to_download_uploaded_file",
                    drive_file_id=uploaded_file.drive_file_id,
                    error=str(e),
                )
                continue

        return images

    async def _find_matching_uploaded_file(
        self, article_id: int, article_image: ArticleImage
    ) -> UploadedFile | None:
        """Find an uploaded_file that matches the article_image.

        Matches by filename or position.
        """
        stmt = select(UploadedFile).where(
            UploadedFile.article_id == article_id,
            UploadedFile.file_type == "image",
        )
        result = await self.session.execute(stmt)
        uploaded_files = result.scalars().all()

        if not uploaded_files:
            return None

        # Try to match by source URL containing drive file ID
        if article_image.source_url:
            for uf in uploaded_files:
                if uf.drive_file_id and uf.drive_file_id in article_image.source_url:
                    return uf

        # Fallback: match by position (index in list)
        if article_image.position < len(uploaded_files):
            return uploaded_files[article_image.position]

        return uploaded_files[0] if uploaded_files else None

    def _guess_mime_type(self, filename: str) -> str:
        """Guess MIME type from filename extension."""
        ext = Path(filename).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".svg": "image/svg+xml",
            ".bmp": "image/bmp",
        }
        return mime_types.get(ext, "image/jpeg")

    def cleanup(self) -> None:
        """Clean up temporary files and directory.

        Should be called after publishing is complete.
        """
        if not self.temp_dir or not self.temp_dir.exists():
            return

        try:
            # Remove all downloaded files
            for image in self.downloaded_files:
                local_path = Path(image["local_path"])
                if local_path.exists():
                    local_path.unlink()
                    logger.debug("removed_temp_file", path=str(local_path))

            # Remove temp directory
            self.temp_dir.rmdir()
            logger.info("cleaned_up_temp_directory", path=str(self.temp_dir))

        except Exception as e:
            logger.warning(
                "cleanup_failed",
                temp_dir=str(self.temp_dir),
                error=str(e),
            )

        finally:
            self.temp_dir = None
            self.downloaded_files.clear()

    def get_image_references_for_replacement(self) -> dict[str, str]:
        """Get mapping of Drive URLs to filenames for article body replacement.

        Returns:
            Dict mapping Drive file IDs/URLs to local filenames

        This can be used to update article body to reference local files
        that Computer Use will upload to WordPress.
        """
        replacements = {}

        for image in self.downloaded_files:
            # Map drive file ID to filename
            replacements[image["drive_file_id"]] = image["filename"]

            # Map web view link to filename
            if image.get("web_view_link"):
                replacements[image["web_view_link"]] = image["filename"]

        return replacements


async def create_drive_image_retriever(session: AsyncSession) -> DriveImageRetriever:
    """Factory function to create DriveImageRetriever.

    Args:
        session: Database session

    Returns:
        DriveImageRetriever instance
    """
    return DriveImageRetriever(session)
