"""Google Drive storage service for file uploads."""

import io
import json
import os
from pathlib import Path
from typing import BinaryIO

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from src.config import get_logger, get_settings

logger = get_logger(__name__)
settings = get_settings()


class GoogleDriveStorage:
    """Google Drive storage backend for file management.

    Uses Service Account authentication for server-to-server access.
    Files are stored in a designated folder with public sharing enabled.
    """

    SCOPES = ["https://www.googleapis.com/auth/drive"]

    def __init__(self) -> None:
        """Initialize Google Drive storage service."""
        self.service = None
        self.folder_id = settings.GOOGLE_DRIVE_FOLDER_ID
        self._initialize_service()

    def _initialize_service(self) -> None:
        """Initialize Google Drive API service with credentials.

        Supports two methods of providing credentials:
        1. GOOGLE_SERVICE_ACCOUNT_JSON environment variable (JSON string) - for Cloud Run
        2. GOOGLE_DRIVE_CREDENTIALS_PATH environment variable (file path) - for local dev
        """
        try:
            # Method 1: Try JSON from environment variable (Cloud Run)
            service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
            if service_account_json:
                logger.info("google_drive_using_json_env_var")
                credentials_info = json.loads(service_account_json)
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_info,
                    scopes=self.SCOPES,
                )
            else:
                # Method 2: Try file path (local development)
                credentials_path = settings.GOOGLE_DRIVE_CREDENTIALS_PATH

                if not credentials_path or not os.path.exists(credentials_path):
                    logger.warning(
                        "google_drive_credentials_not_found",
                        path=credentials_path,
                    )
                    raise ValueError(
                        "Google Drive credentials not found. "
                        "Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_DRIVE_CREDENTIALS_PATH environment variable."
                    )

                logger.info("google_drive_using_credentials_file", path=credentials_path)
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path,
                    scopes=self.SCOPES,
                )

            # Build Drive API service
            self.service = build("drive", "v3", credentials=credentials)

            logger.info("google_drive_service_initialized")

        except Exception as e:
            logger.error(
                "google_drive_initialization_failed",
                error=str(e),
                exc_info=True,
            )
            raise

    async def upload_file(
        self,
        file_content: BinaryIO,
        filename: str,
        mime_type: str = "application/octet-stream",
        folder_id: str | None = None,
    ) -> dict:
        """Upload file to Google Drive.

        Args:
            file_content: File content as bytes or file-like object
            filename: Name for the file in Drive
            mime_type: MIME type of the file
            folder_id: Optional parent folder ID (uses default if None)

        Returns:
            dict: File metadata with id, name, webViewLink, webContentLink

        Raises:
            Exception: If upload fails
        """
        try:
            target_folder = folder_id or self.folder_id

            # Prepare file metadata
            file_metadata = {
                "name": filename,
                "parents": [target_folder] if target_folder else [],
            }

            # Create media upload
            media = MediaIoBaseUpload(
                file_content,
                mimetype=mime_type,
                resumable=True,
            )

            # Upload file
            file = (
                self.service.files()
                .create(
                    body=file_metadata,
                    media_body=media,
                    fields="id,name,mimeType,size,webViewLink,webContentLink,createdTime",
                )
                .execute()
            )

            # Make file publicly accessible
            await self._make_public(file["id"])

            logger.info(
                "google_drive_file_uploaded",
                file_id=file["id"],
                filename=filename,
                size=file.get("size"),
            )

            return file

        except Exception as e:
            logger.error(
                "google_drive_upload_failed",
                filename=filename,
                error=str(e),
                exc_info=True,
            )
            raise

    async def upload_file_from_path(
        self,
        file_path: str,
        filename: str | None = None,
        folder_id: str | None = None,
    ) -> dict:
        """Upload file from local path to Google Drive.

        Args:
            file_path: Path to local file
            filename: Optional custom filename (uses file basename if None)
            folder_id: Optional parent folder ID

        Returns:
            dict: File metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            Exception: If upload fails
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if filename is None:
            filename = path.name

        # Detect MIME type
        mime_type = self._get_mime_type(filename)

        with open(path, "rb") as f:
            return await self.upload_file(
                file_content=f,
                filename=filename,
                mime_type=mime_type,
                folder_id=folder_id,
            )

    async def download_file(self, file_id: str) -> bytes:
        """Download file content from Google Drive.

        Args:
            file_id: Google Drive file ID

        Returns:
            bytes: File content

        Raises:
            Exception: If download fails
        """
        try:
            request = self.service.files().get_media(fileId=file_id)

            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(
                        "google_drive_download_progress",
                        file_id=file_id,
                        progress=int(status.progress() * 100),
                    )

            file_content.seek(0)

            logger.info(
                "google_drive_file_downloaded",
                file_id=file_id,
                size=len(file_content.getvalue()),
            )

            return file_content.getvalue()

        except Exception as e:
            logger.error(
                "google_drive_download_failed",
                file_id=file_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def download_to_path(self, file_id: str, destination_path: str) -> str:
        """Download file from Google Drive to local path.

        Args:
            file_id: Google Drive file ID
            destination_path: Local path to save file

        Returns:
            str: Path to downloaded file

        Raises:
            Exception: If download fails
        """
        content = await self.download_file(file_id)

        destination = Path(destination_path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        with open(destination, "wb") as f:
            f.write(content)

        logger.info(
            "google_drive_file_saved",
            file_id=file_id,
            path=str(destination),
        )

        return str(destination)

    async def get_file_metadata(self, file_id: str) -> dict:
        """Get file metadata from Google Drive.

        Args:
            file_id: Google Drive file ID

        Returns:
            dict: File metadata

        Raises:
            Exception: If request fails
        """
        try:
            file = (
                self.service.files()
                .get(
                    fileId=file_id,
                    fields="id,name,mimeType,size,webViewLink,webContentLink,createdTime,modifiedTime",
                )
                .execute()
            )

            return file

        except Exception as e:
            logger.error(
                "google_drive_metadata_failed",
                file_id=file_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def get_public_url(self, file_id: str) -> str:
        """Get public URL for file viewing.

        Args:
            file_id: Google Drive file ID

        Returns:
            str: Public URL for file

        Raises:
            Exception: If request fails
        """
        file = await self.get_file_metadata(file_id)
        return file.get("webContentLink") or file.get("webViewLink")

    async def delete_file(self, file_id: str) -> bool:
        """Delete file from Google Drive.

        Args:
            file_id: Google Drive file ID

        Returns:
            bool: True if deleted successfully

        Raises:
            Exception: If deletion fails
        """
        try:
            self.service.files().delete(fileId=file_id).execute()

            logger.info("google_drive_file_deleted", file_id=file_id)

            return True

        except Exception as e:
            logger.error(
                "google_drive_delete_failed",
                file_id=file_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def _make_public(self, file_id: str) -> None:
        """Make file publicly accessible (anyone with link can view).

        Args:
            file_id: Google Drive file ID

        Raises:
            Exception: If permission update fails
        """
        try:
            permission = {
                "type": "anyone",
                "role": "reader",
            }

            self.service.permissions().create(
                fileId=file_id,
                body=permission,
            ).execute()

            logger.debug("google_drive_file_made_public", file_id=file_id)

        except Exception as e:
            logger.warning(
                "google_drive_make_public_failed",
                file_id=file_id,
                error=str(e),
            )
            # Don't raise - file is still uploaded

    def _get_mime_type(self, filename: str) -> str:
        """Get MIME type from filename extension.

        Args:
            filename: Filename with extension

        Returns:
            str: MIME type
        """
        extension = Path(filename).suffix.lower()

        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".svg": "image/svg+xml",
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".txt": "text/plain",
            ".csv": "text/csv",
            ".json": "application/json",
            ".zip": "application/zip",
        }

        return mime_types.get(extension, "application/octet-stream")

    async def list_files(self, folder_id: str | None = None, max_results: int = 100) -> list[dict]:
        """List files in folder.

        Args:
            folder_id: Folder ID to list (uses default if None)
            max_results: Maximum number of files to return

        Returns:
            list[dict]: List of file metadata

        Raises:
            Exception: If request fails
        """
        try:
            target_folder = folder_id or self.folder_id

            query = f"'{target_folder}' in parents and trashed=false"

            results = (
                self.service.files()
                .list(
                    q=query,
                    pageSize=max_results,
                    fields="files(id,name,mimeType,size,webViewLink,createdTime)",
                )
                .execute()
            )

            files = results.get("files", [])

            logger.info(
                "google_drive_files_listed",
                folder_id=target_folder,
                count=len(files),
            )

            return files

        except Exception as e:
            logger.error(
                "google_drive_list_failed",
                folder_id=folder_id,
                error=str(e),
                exc_info=True,
            )
            raise


async def create_google_drive_storage() -> GoogleDriveStorage:
    """Factory function for Google Drive storage service.

    Returns:
        GoogleDriveStorage: Configured service instance

    Raises:
        ValueError: If credentials not configured
    """
    return GoogleDriveStorage()
