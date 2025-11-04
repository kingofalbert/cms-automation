"""Article import API routes."""

import os
import tempfile
from pathlib import Path

from celery.result import AsyncResult
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from src.api.schemas.import_schema import (
    ImportInitiateResponse,
    ImportResultSchema,
    ImportTaskStatusSchema,
)
from src.config.logging import get_logger
from src.workers.celery_app import celery_app

router = APIRouter()
logger = get_logger(__name__)


@router.post("/import", response_model=ImportInitiateResponse, status_code=status.HTTP_202_ACCEPTED)
async def import_articles(
    file: UploadFile = File(..., description="Import file (CSV, JSON, or WordPress XML)"),
    file_format: str | None = Form(
        None,
        description="File format (csv, json, wordpress). Auto-detected if not provided.",
    ),
) -> ImportInitiateResponse:
    """Import articles from uploaded file.

    Supports:
        - CSV files (.csv)
        - JSON files (.json)
        - WordPress exports (.xml, .wxr)

    The import process runs asynchronously. Use the returned task_id to check status.

    Args:
        file: Upload file
        file_format: Optional format override (csv, json, wordpress)

    Returns:
        ImportInitiateResponse with task_id for tracking

    Raises:
        HTTPException: If file format is unsupported or upload fails
    """
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    # Auto-detect format from filename if not provided
    if file_format is None:
        extension = Path(file.filename).suffix.lower()
        format_map = {
            ".csv": "csv",
            ".json": "json",
            ".xml": "wordpress",
            ".wxr": "wordpress",
        }
        file_format = format_map.get(extension)

        if not file_format:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file extension: {extension}. "
                f"Supported: .csv, .json, .xml, .wxr",
            )

    # Validate format
    if file_format not in ["csv", "json", "wordpress"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file_format: {file_format}. "
            f"Supported formats: csv, json, wordpress",
        )

    # Save uploaded file to temporary location
    try:
        # Create temp directory if it doesn't exist
        temp_dir = Path(tempfile.gettempdir()) / "cms_imports"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        temp_file = temp_dir / f"import_{os.urandom(8).hex()}_{file.filename}"

        # Save file
        with open(temp_file, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(
            "import_file_uploaded",
            filename=file.filename,
            format=file_format,
            size=len(content),
            temp_path=str(temp_file),
        )

    except Exception as e:
        logger.error(
            "import_file_upload_failed",
            filename=file.filename,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}",
        )

    # Queue import task
    try:
        # Lazy import to avoid circular dependency
        from src.workers.tasks import import_articles_task

        task = import_articles_task.delay(
            file_path=str(temp_file),
            file_format=file_format,
        )

        logger.info(
            "import_task_queued",
            task_id=task.id,
            filename=file.filename,
            format=file_format,
        )

        return ImportInitiateResponse(
            task_id=task.id,
            message=f"Import task queued for {file.filename}",
            status_url=f"/v1/import/status/{task.id}",
        )

    except Exception as e:
        logger.error(
            "import_task_queue_failed",
            filename=file.filename,
            error=str(e),
            exc_info=True,
        )

        # Clean up temp file
        if temp_file.exists():
            temp_file.unlink()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue import task: {str(e)}",
        )


@router.get("/import/status/{task_id}", response_model=ImportTaskStatusSchema)
async def get_import_status(task_id: str) -> ImportTaskStatusSchema:
    """Get status of import task.

    Args:
        task_id: Celery task ID

    Returns:
        ImportTaskStatusSchema with task status and result

    Raises:
        HTTPException: If task not found
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)

        # Map Celery states to our status
        status_map = {
            "PENDING": "pending",
            "STARTED": "running",
            "SUCCESS": "completed",
            "FAILURE": "failed",
            "RETRY": "running",
            "REVOKED": "failed",
        }

        status_value = status_map.get(task_result.state, "unknown")

        response = ImportTaskStatusSchema(
            task_id=task_id,
            status=status_value,
        )

        # Add result if completed
        if task_result.state == "SUCCESS":
            result_data = task_result.result
            if result_data:
                response.result = ImportResultSchema(**result_data)

        # Add error if failed
        elif task_result.state == "FAILURE":
            response.error = str(task_result.result)

        logger.debug(
            "import_status_checked",
            task_id=task_id,
            status=status_value,
        )

        return response

    except Exception as e:
        logger.error(
            "import_status_check_failed",
            task_id=task_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check task status: {str(e)}",
        )


@router.delete("/import/{task_id}")
async def cancel_import_task(task_id: str) -> dict[str, str]:
    """Cancel a running import task.

    Args:
        task_id: Celery task ID

    Returns:
        dict with cancellation status

    Raises:
        HTTPException: If task cannot be cancelled
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)

        if task_result.state in ["SUCCESS", "FAILURE"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel {task_result.state.lower()} task",
            )

        # Revoke the task
        task_result.revoke(terminate=True)

        logger.info("import_task_cancelled", task_id=task_id)

        return {
            "message": f"Import task {task_id} cancelled",
            "status": "cancelled",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "import_task_cancel_failed",
            task_id=task_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}",
        )
