"""Topic request API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.topic_request import (
    TopicRequestCreate,
    TopicRequestListResponse,
    TopicRequestResponse,
)
from src.config.database import get_session
from src.models import TopicRequest

router = APIRouter()


@router.post(
    "",
    response_model=TopicRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_topic_request(
    topic_data: TopicRequestCreate,
    session: AsyncSession = Depends(get_session),
) -> TopicRequest:
    """Submit a new topic for article generation.

    Args:
        topic_data: Topic request data
        session: Database session

    Returns:
        TopicRequest: Created topic request
    """
    # Create topic request
    topic_request = TopicRequest(
        title=topic_data.title,
        outline=topic_data.outline,
        style_tone=topic_data.style_tone,
        target_word_count=topic_data.target_word_count,
        priority=topic_data.priority,
        submitted_by=1,  # TODO: Get from auth middleware
    )

    session.add(topic_request)
    await session.commit()
    await session.refresh(topic_request)

    # Dispatch background task for article generation
    # Lazy import to avoid circular dependency
    from src.workers.tasks.generate_article import generate_article_task

    generate_article_task.delay(topic_request.id)

    return topic_request


@router.get("", response_model=list[TopicRequestListResponse])
async def list_topic_requests(
    skip: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
) -> list[TopicRequest]:
    """List topic requests.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        session: Database session

    Returns:
        list[TopicRequest]: List of topic requests
    """
    result = await session.execute(
        select(TopicRequest)
        .order_by(TopicRequest.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/{topic_id}", response_model=TopicRequestResponse)
async def get_topic_request(
    topic_id: int,
    session: AsyncSession = Depends(get_session),
) -> TopicRequest:
    """Get a specific topic request.

    Args:
        topic_id: Topic request ID
        session: Database session

    Returns:
        TopicRequest: Topic request details

    Raises:
        HTTPException: If topic request not found
    """
    result = await session.execute(
        select(TopicRequest).where(TopicRequest.id == topic_id)
    )
    topic_request = result.scalar_one_or_none()

    if not topic_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic request {topic_id} not found",
        )

    return topic_request
