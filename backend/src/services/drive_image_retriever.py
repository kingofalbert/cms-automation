"""Service for retrieving images from Google Drive for publishing."""

import tempfile
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_logger
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
        """Get all images associated with an article from Google Drive.

        Args:
            article_id: Article ID to fetch images for

        Returns:
            List of image metadata dicts with local file paths

        Example return:
        [
            {
                "drive_file_id": "abc123",
                "filename": "image1.jpg",
                "mime_type": "image/jpeg",
                "local_path": "/tmp/images/image1.jpg",
                "web_view_link": "https://drive.google.com/...",
            }
        ]
        """
        logger.info("retrieving_article_images", article_id=article_id)

        # Query uploaded_files for article images
        stmt = select(UploadedFile).where(
            UploadedFile.article_id == article_id,
            UploadedFile.file_type == "image",
        )
        result = await self.session.execute(stmt)
        uploaded_files = result.scalars().all()

        if not uploaded_files:
            logger.info("no_images_found_for_article", article_id=article_id)
            return []

        logger.info(
            "found_article_images",
            article_id=article_id,
            count=len(uploaded_files),
        )

        # Create temp directory for downloads
        self.temp_dir = Path(tempfile.mkdtemp(prefix="cms_images_"))
        logger.debug("created_temp_directory", path=str(self.temp_dir))

        # Download images from Google Drive
        storage = await create_google_drive_storage()
        images = []

        for uploaded_file in uploaded_files:
            try:
                # Download from Google Drive
                file_data = await storage.download_file(uploaded_file.drive_file_id)

                # Save to temp file
                local_path = self.temp_dir / uploaded_file.filename
                local_path.write_bytes(file_data)

                image_metadata = {
                    "drive_file_id": uploaded_file.drive_file_id,
                    "filename": uploaded_file.filename,
                    "mime_type": uploaded_file.mime_type,
                    "local_path": str(local_path),
                    "web_view_link": uploaded_file.web_view_link,
                    "file_size": uploaded_file.file_size,
                }

                images.append(image_metadata)
                self.downloaded_files.append(image_metadata)

                logger.debug(
                    "image_downloaded_from_drive",
                    drive_file_id=uploaded_file.drive_file_id,
                    filename=uploaded_file.filename,
                    local_path=str(local_path),
                )

            except Exception as e:
                logger.error(
                    "failed_to_download_image",
                    drive_file_id=uploaded_file.drive_file_id,
                    filename=uploaded_file.filename,
                    error=str(e),
                    exc_info=True,
                )
                # Continue with other images
                continue

        logger.info(
            "article_images_retrieved",
            article_id=article_id,
            total=len(uploaded_files),
            downloaded=len(images),
        )

        return images

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
