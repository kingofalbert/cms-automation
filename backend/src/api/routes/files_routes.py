"""API routes for file upload and management via Google Drive."""

import io
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.file_upload import (
    BulkUploadResponse,
    FileDeleteResponse,
    FileListResponse,
    FileMetadataResponse,
    FileUploadResponse,
)
from src.config import get_logger
from src.config.database import get_session
from src.models.uploaded_file import UploadedFile
from src.services.storage import create_google_drive_storage

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/files", tags=["files"])


def _classify_file_type(mime_type: str) -> str:
    """Classify file type based on MIME type."""
    if mime_type.startswith("image/"):
        return "image"
    elif mime_type.startswith("video/"):
        return "video"
    elif mime_type in [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    ]:
        return "document"
    else:
        return "other"


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload file to Google Drive",
)
async def upload_file(
    file: UploadFile = File(..., description="File to upload"),
    article_id: Optional[int] = Form(None, description="Associated article ID"),
    file_type: Optional[str] = Form(None, description="File type classification"),
    folder_id: Optional[str] = Form(None, description="Google Drive folder ID"),
    session: AsyncSession = Depends(get_session),
) -> FileUploadResponse:
    """Upload a file to Google Drive and track it in the database.

    Args:
        file: File to upload (multipart/form-data)
        article_id: Optional article ID to associate with the file
        file_type: Optional file type override (image, document, video, other)
        folder_id: Optional Google Drive folder ID (uses default if not provided)
        session: Database session

    Returns:
        FileUploadResponse with upload details
    """
    try:
        # Read file content
        content = await file.read()
        file_content = io.BytesIO(content)

        # Determine MIME type
        mime_type = file.content_type or "application/octet-stream"

        # Classify file type
        classified_type = file_type or _classify_file_type(mime_type)

        # Upload to Google Drive
        storage = await create_google_drive_storage()
        drive_file = await storage.upload_file(
            file_content=file_content,
            filename=file.filename,
            mime_type=mime_type,
            folder_id=folder_id,
        )

        # Create database record
        uploaded_file = UploadedFile(
            filename=file.filename,
            drive_file_id=drive_file["id"],
            drive_folder_id=folder_id,
            mime_type=mime_type,
            file_size=len(content),
            web_view_link=drive_file.get("webViewLink"),
            web_content_link=drive_file.get("webContentLink"),
            article_id=article_id,
            file_type=classified_type,
            file_metadata={
                "original_mime_type": file.content_type,
                "upload_size_bytes": len(content),
            },
        )

        session.add(uploaded_file)
        await session.commit()
        await session.refresh(uploaded_file)

        logger.info(
            "file_uploaded",
            file_id=uploaded_file.id,
            drive_file_id=drive_file["id"],
            filename=file.filename,
            size=len(content),
        )

        return FileUploadResponse(
            file_id=uploaded_file.id,
            drive_file_id=uploaded_file.drive_file_id,
            filename=uploaded_file.filename,
            file_type=uploaded_file.file_type,
            mime_type=uploaded_file.mime_type,
            file_size=uploaded_file.file_size,
            web_view_link=uploaded_file.web_view_link,
            web_content_link=uploaded_file.web_content_link,
            public_url=uploaded_file.public_url,
            article_id=uploaded_file.article_id,
            created_at=uploaded_file.created_at,
        )

    except Exception as e:
        logger.error(
            "file_upload_failed",
            filename=file.filename,
            error=str(e),
            exc_info=True,
        )
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}",
        )


@router.post(
    "/upload-bulk",
    response_model=BulkUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload multiple files to Google Drive",
)
async def upload_bulk_files(
    files: list[UploadFile] = File(..., description="Files to upload"),
    article_id: Optional[int] = Form(None, description="Associated article ID"),
    folder_id: Optional[str] = Form(None, description="Google Drive folder ID"),
    session: AsyncSession = Depends(get_session),
) -> BulkUploadResponse:
    """Upload multiple files to Google Drive in bulk.

    Args:
        files: List of files to upload
        article_id: Optional article ID to associate with all files
        folder_id: Optional Google Drive folder ID
        session: Database session

    Returns:
        BulkUploadResponse with upload results
    """
    successful_uploads = []
    failed_uploads = []

    for file in files:
        try:
            # Read file content
            content = await file.read()
            file_content = io.BytesIO(content)

            # Determine MIME type
            mime_type = file.content_type or "application/octet-stream"
            classified_type = _classify_file_type(mime_type)

            # Upload to Google Drive
            storage = await create_google_drive_storage()
            drive_file = await storage.upload_file(
                file_content=file_content,
                filename=file.filename,
                mime_type=mime_type,
                folder_id=folder_id,
            )

            # Create database record
            uploaded_file = UploadedFile(
                filename=file.filename,
                drive_file_id=drive_file["id"],
                drive_folder_id=folder_id,
                mime_type=mime_type,
                file_size=len(content),
                web_view_link=drive_file.get("webViewLink"),
                web_content_link=drive_file.get("webContentLink"),
                article_id=article_id,
                file_type=classified_type,
            )

            session.add(uploaded_file)
            await session.commit()
            await session.refresh(uploaded_file)

            successful_uploads.append(
                FileUploadResponse(
                    file_id=uploaded_file.id,
                    drive_file_id=uploaded_file.drive_file_id,
                    filename=uploaded_file.filename,
                    file_type=uploaded_file.file_type,
                    mime_type=uploaded_file.mime_type,
                    file_size=uploaded_file.file_size,
                    web_view_link=uploaded_file.web_view_link,
                    web_content_link=uploaded_file.web_content_link,
                    public_url=uploaded_file.public_url,
                    article_id=uploaded_file.article_id,
                    created_at=uploaded_file.created_at,
                )
            )

        except Exception as e:
            logger.error(
                "bulk_file_upload_failed",
                filename=file.filename,
                error=str(e),
            )
            failed_uploads.append(
                {
                    "filename": file.filename,
                    "error": str(e),
                }
            )
            await session.rollback()
            continue

    logger.info(
        "bulk_file_upload_completed",
        total_uploaded=len(successful_uploads),
        total_failed=len(failed_uploads),
    )

    return BulkUploadResponse(
        successful_uploads=successful_uploads,
        failed_uploads=failed_uploads,
        total_uploaded=len(successful_uploads),
        total_failed=len(failed_uploads),
    )


@router.get(
    "/{file_id}",
    response_model=FileMetadataResponse,
    summary="Get file metadata",
)
async def get_file_metadata(
    file_id: int,
    session: AsyncSession = Depends(get_session),
) -> FileMetadataResponse:
    """Get metadata for an uploaded file.

    Args:
        file_id: Database file ID
        session: Database session

    Returns:
        FileMetadataResponse with file details
    """
    uploaded_file = await session.get(UploadedFile, file_id)

    if not uploaded_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found",
        )

    return FileMetadataResponse(
        file_id=uploaded_file.id,
        filename=uploaded_file.filename,
        drive_file_id=uploaded_file.drive_file_id,
        drive_folder_id=uploaded_file.drive_folder_id,
        mime_type=uploaded_file.mime_type,
        file_size=uploaded_file.file_size,
        file_type=uploaded_file.file_type,
        web_view_link=uploaded_file.web_view_link,
        web_content_link=uploaded_file.web_content_link,
        public_url=uploaded_file.public_url,
        article_id=uploaded_file.article_id,
        uploaded_by=uploaded_file.uploaded_by,
        file_metadata=uploaded_file.file_metadata,
        created_at=uploaded_file.created_at,
        updated_at=uploaded_file.updated_at,
    )


@router.get(
    "/",
    response_model=FileListResponse,
    summary="List uploaded files",
)
async def list_files(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Files per page"),
    article_id: Optional[int] = Query(None, description="Filter by article ID"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    session: AsyncSession = Depends(get_session),
) -> FileListResponse:
    """List uploaded files with pagination and filtering.

    Args:
        page: Page number (1-indexed)
        page_size: Number of files per page
        article_id: Optional filter by article ID
        file_type: Optional filter by file type (image, document, video, other)
        session: Database session

    Returns:
        FileListResponse with paginated file list
    """
    from sqlalchemy import select, func

    # Build query
    query = select(UploadedFile).where(UploadedFile.deleted_at.is_(None))

    if article_id is not None:
        query = query.where(UploadedFile.article_id == article_id)

    if file_type:
        query = query.where(UploadedFile.file_type == file_type)

    # Count total
    count_query = select(func.count()).select_from(UploadedFile).where(UploadedFile.deleted_at.is_(None))
    if article_id is not None:
        count_query = count_query.where(UploadedFile.article_id == article_id)
    if file_type:
        count_query = count_query.where(UploadedFile.file_type == file_type)

    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(UploadedFile.created_at.desc())

    # Execute query
    result = await session.execute(query)
    files = result.scalars().all()

    return FileListResponse(
        files=[
            FileMetadataResponse(
                file_id=f.id,
                filename=f.filename,
                drive_file_id=f.drive_file_id,
                drive_folder_id=f.drive_folder_id,
                mime_type=f.mime_type,
                file_size=f.file_size,
                file_type=f.file_type,
                web_view_link=f.web_view_link,
                web_content_link=f.web_content_link,
                public_url=f.public_url,
                article_id=f.article_id,
                uploaded_by=f.uploaded_by,
                file_metadata=f.file_metadata,
                created_at=f.created_at,
                updated_at=f.updated_at,
            )
            for f in files
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete(
    "/{file_id}",
    response_model=FileDeleteResponse,
    summary="Delete file",
)
async def delete_file(
    file_id: int,
    hard_delete: bool = Query(False, description="Permanently delete file from Google Drive"),
    session: AsyncSession = Depends(get_session),
) -> FileDeleteResponse:
    """Delete an uploaded file (soft delete by default, or hard delete from Drive).

    Args:
        file_id: Database file ID
        hard_delete: If True, delete from Google Drive; if False, soft delete
        session: Database session

    Returns:
        FileDeleteResponse with deletion status
    """
    uploaded_file = await session.get(UploadedFile, file_id)

    if not uploaded_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found",
        )

    try:
        if hard_delete:
            # Delete from Google Drive
            storage = await create_google_drive_storage()
            await storage.delete_file(uploaded_file.drive_file_id)

            # Delete from database
            await session.delete(uploaded_file)
            message = f"File {file_id} permanently deleted from Google Drive and database"
        else:
            # Soft delete
            uploaded_file.mark_deleted()
            message = f"File {file_id} soft deleted (marked as deleted)"

        await session.commit()

        logger.info(
            "file_deleted",
            file_id=file_id,
            drive_file_id=uploaded_file.drive_file_id,
            hard_delete=hard_delete,
        )

        return FileDeleteResponse(
            file_id=file_id,
            drive_file_id=uploaded_file.drive_file_id,
            deleted=True,
            message=message,
        )

    except Exception as e:
        logger.error(
            "file_deletion_failed",
            file_id=file_id,
            error=str(e),
            exc_info=True,
        )
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File deletion failed: {str(e)}",
        )
