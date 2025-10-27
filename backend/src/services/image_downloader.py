"""Image downloader service for importing images from URLs to Google Drive."""

import io
from typing import Optional
from urllib.parse import urlparse

import httpx

from src.config import get_logger
from src.models.uploaded_file import UploadedFile
from src.services.storage import create_google_drive_storage

logger = get_logger(__name__)


class ImageDownloader:
    """Download images from URLs and upload to Google Drive."""

    def __init__(self) -> None:
        """Initialize image downloader."""
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )

    async def download_and_upload(
        self,
        image_url: str,
        article_id: Optional[int] = None,
        filename: Optional[str] = None,
    ) -> UploadedFile:
        """Download image from URL and upload to Google Drive.

        Args:
            image_url: URL of image to download
            article_id: Optional article ID to associate with the image
            filename: Optional custom filename (extracted from URL if None)

        Returns:
            UploadedFile instance with Drive metadata

        Raises:
            httpx.HTTPError: If download fails
            Exception: If upload fails
        """
        try:
            # Download image
            logger.info(
                "downloading_image",
                url=image_url,
                article_id=article_id,
            )

            response = await self.http_client.get(image_url)
            response.raise_for_status()

            # Get filename from URL if not provided
            if filename is None:
                filename = self._extract_filename(image_url)

            # Get MIME type from response
            mime_type = response.headers.get("content-type", "application/octet-stream")
            # Remove charset if present
            if ";" in mime_type:
                mime_type = mime_type.split(";")[0].strip()

            # Get file size
            file_size = len(response.content)

            logger.debug(
                "image_downloaded",
                url=image_url,
                filename=filename,
                mime_type=mime_type,
                size=file_size,
            )

            # Upload to Google Drive
            storage = await create_google_drive_storage()
            file_content = io.BytesIO(response.content)

            drive_file = await storage.upload_file(
                file_content=file_content,
                filename=filename,
                mime_type=mime_type,
            )

            # Create UploadedFile record
            uploaded_file = UploadedFile(
                filename=filename,
                drive_file_id=drive_file["id"],
                drive_folder_id=drive_file.get("parents", [None])[0] if drive_file.get("parents") else None,
                mime_type=mime_type,
                file_size=file_size,
                web_view_link=drive_file.get("webViewLink"),
                web_content_link=drive_file.get("webContentLink"),
                article_id=article_id,
                file_type="image" if mime_type.startswith("image/") else "other",
                file_metadata={
                    "source_url": image_url,
                    "download_size_bytes": file_size,
                },
            )

            logger.info(
                "image_uploaded_to_drive",
                url=image_url,
                drive_file_id=drive_file["id"],
                article_id=article_id,
            )

            return uploaded_file

        except httpx.HTTPError as e:
            logger.error(
                "image_download_failed",
                url=image_url,
                error=str(e),
                exc_info=True,
            )
            raise

        except Exception as e:
            logger.error(
                "image_upload_failed",
                url=image_url,
                error=str(e),
                exc_info=True,
            )
            raise

    def _extract_filename(self, url: str) -> str:
        """Extract filename from URL.

        Args:
            url: Image URL

        Returns:
            Filename extracted from URL
        """
        parsed = urlparse(url)
        path = parsed.path

        # Get last part of path
        if "/" in path:
            filename = path.split("/")[-1]
        else:
            filename = path

        # Remove query parameters
        if "?" in filename:
            filename = filename.split("?")[0]

        # Use default if empty
        if not filename or filename == "/":
            filename = "image.jpg"

        # Sanitize filename
        filename = self._sanitize_filename(filename)

        return filename

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to remove dangerous characters.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove path traversal attempts
        filename = filename.replace("..", "").replace("/", "_").replace("\\", "_")

        # Keep only alphanumeric, dots, hyphens, underscores
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_")
        filename = "".join(c if c in allowed_chars else "_" for c in filename)

        # Ensure it has an extension
        if "." not in filename:
            filename = f"{filename}.jpg"

        return filename

    async def close(self) -> None:
        """Close HTTP client."""
        await self.http_client.aclose()


async def create_image_downloader() -> ImageDownloader:
    """Factory function to create ImageDownloader instance.

    Returns:
        ImageDownloader instance
    """
    return ImageDownloader()
