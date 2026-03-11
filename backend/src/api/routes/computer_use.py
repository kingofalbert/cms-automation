"""API routes for Computer Use CMS operations."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.config import get_logger, get_settings

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(prefix="/computer-use", tags=["Computer Use"])


class PublishArticleRequest(BaseModel):
    """Request schema for publishing article via Computer Use."""

    article_id: int = Field(..., gt=0, description="Article ID to publish")
    cms_url: str | None = Field(
        default=None,
        description="CMS admin URL (defaults to settings.CMS_BASE_URL)",
    )
    cms_username: str | None = Field(
        default=None,
        description="CMS username (defaults to settings.CMS_USERNAME)",
    )
    cms_password: str | None = Field(
        default=None,
        description="CMS password (defaults to settings.CMS_APPLICATION_PASSWORD)",
    )
    cms_type: str = Field(
        default="wordpress",
        description="CMS platform type",
    )
    publishing_strategy: str = Field(
        default="auto",
        description="Publishing strategy: auto, computer_use, playwright, cost_optimized, quality_optimized",
    )


class PublishArticleResponse(BaseModel):
    """Response schema for publish article request."""

    task_id: str = Field(..., description="Celery task ID for tracking")
    message: str = Field(..., description="Status message")
    article_id: int = Field(..., description="Article ID being published")


class TaskStatusResponse(BaseModel):
    """Response schema for task status check."""

    task_id: str
    status: str
    result: dict | None = None
    error: str | None = None


@router.post("/publish", response_model=PublishArticleResponse, status_code=status.HTTP_202_ACCEPTED)
async def publish_article_with_computer_use(
    request: PublishArticleRequest,
) -> PublishArticleResponse:
    """Publish article using Computer Use API.

    This endpoint triggers an async Celery task that will use Claude's Computer Use API
    to navigate to the CMS admin panel, log in, create a new post, configure SEO settings,
    and publish the article.

    Args:
        request: Publishing request with article ID and optional CMS credentials

    Returns:
        PublishArticleResponse: Task information for tracking

    Raises:
        HTTPException: If article ID is invalid or request fails
    """
    # Use settings defaults if not provided
    cms_url = request.cms_url or settings.CMS_BASE_URL
    cms_username = request.cms_username or settings.CMS_USERNAME
    cms_password = request.cms_password or settings.CMS_APPLICATION_PASSWORD

    if not cms_url or not cms_username or not cms_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CMS credentials not provided and not found in settings",
        )

    logger.info(
        "computer_use_publish_requested",
        article_id=request.article_id,
        cms_type=request.cms_type,
    )

    # Celery workers have been removed — return 501
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Computer Use publishing via Celery is no longer available. Use the Playwright publisher at POST /v1/worklist/{item_id}/publish instead.",
    )


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """Get status of a Computer Use publishing task.

    Args:
        task_id: Celery task ID

    Returns:
        TaskStatusResponse: Current task status and result

    Raises:
        HTTPException: If task ID is not found
    """
    from celery.result import AsyncResult

    task_result = AsyncResult(task_id)

    logger.info(
        "computer_use_task_status_checked",
        task_id=task_id,
        status=task_result.status,
    )

    response_data = {
        "task_id": task_id,
        "status": task_result.status,
        "result": None,
        "error": None,
    }

    if task_result.ready():
        if task_result.successful():
            response_data["result"] = task_result.result
        else:
            response_data["error"] = str(task_result.info)

    return TaskStatusResponse(**response_data)


@router.post("/test-environment")
async def test_computer_use_environment() -> dict:
    """Test that Computer Use environment is properly configured.

    This endpoint checks:
    - Display server (X11/Xvfb) is running
    - VNC server is accessible
    - Browser (Chromium) is installed
    - Anthropic API key is configured

    Returns:
        dict: Test results for each component
    """
    logger.info("computer_use_environment_test_requested")

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Computer Use environment test is no longer available (Celery removed).",
    )
