"""Article API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.article import ArticleListResponse, ArticleResponse
from src.config.database import get_session
from src.models import Article

router = APIRouter()


@router.get("", response_model=list[ArticleListResponse])
async def list_articles(
    skip: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
) -> list[Article]:
    """List articles.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        session: Database session

    Returns:
        list[Article]: List of articles
    """
    result = await session.execute(
        select(Article)
        .order_by(Article.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: int,
    session: AsyncSession = Depends(get_session),
) -> Article:
    """Get a specific article.

    Args:
        article_id: Article ID
        session: Database session

    Returns:
        Article: Article details

    Raises:
        HTTPException: If article not found
    """
    result = await session.execute(
        select(Article).where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found",
        )

    return article
