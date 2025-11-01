"""Article API routes."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import ProofreadingResponse
from src.api.schemas.article import ArticleListResponse, ArticleResponse
from src.config.database import get_session
from src.config.logging import get_logger
from src.models import Article
from src.services.proofreading import (
    ArticlePayload,
    ArticleSection,
    ImageMetadata,
    ProofreadingAnalysisService,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=list[ArticleListResponse])
async def list_articles(
    skip: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
) -> list[Article]:
    """List articles."""
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
    """Get a specific article."""
    article = await _fetch_article(session, article_id)
    return article


@router.post("/{article_id}/proofread", response_model=ProofreadingResponse)
async def proofread_article(
    article_id: int,
    session: AsyncSession = Depends(get_session),
) -> ProofreadingResponse:
    """Run unified proofreading (AI + deterministic checks) for an article."""
    article = await _fetch_article(session, article_id)
    payload = _build_article_payload(article)
    service = _get_proofreading_service()

    try:
        result = await service.analyze_article(payload)
    except Exception as exc:  # noqa: BLE001 - propagate as HTTP error
        logger.error(
            "proofreading_analysis_failed",
            article_id=article_id,
            error=str(exc),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Proofreading analysis failed. Please retry later.",
        ) from exc

    article.proofreading_issues = [
        issue.model_dump(mode="json") for issue in result.issues
    ]
    article.critical_issues_count = result.statistics.blocking_issue_count
    article.article_metadata = _merge_proofreading_metadata(
        article.article_metadata, result.model_dump(mode="json")
    )

    session.add(article)
    await session.commit()

    return ProofreadingResponse.model_validate(result.model_dump())


async def _fetch_article(session: AsyncSession, article_id: int) -> Article:
    """Fetch article or raise 404."""
    result = await session.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found",
        )
    return article


def _build_article_payload(article: Article) -> ArticlePayload:
    """Convert Article ORM object to Proofreading service payload."""
    metadata = dict(article.article_metadata or {})
    sections = _extract_article_sections(metadata, article.body or "")
    featured_image = _build_featured_image_metadata(article, metadata)
    images = _build_inline_images(article, metadata)
    keywords = _extract_keywords(metadata)
    html_content = (
        metadata.get("rendered_html")
        or metadata.get("html")
        or metadata.get("body_html")
        or article.body
    )
    target_locale = (
        metadata.get("locale")
        or metadata.get("language")
        or metadata.get("target_locale")
        or "zh-TW"
    )

    return ArticlePayload(
        article_id=article.id,
        title=article.title,
        original_content=article.body or "",
        html_content=html_content,
        sections=sections,
        metadata=metadata,
        featured_image=featured_image,
        images=images,
        keywords=keywords,
        target_locale=target_locale,
    )


def _extract_article_sections(metadata: dict[str, Any], body: str) -> list[ArticleSection]:
    """Build structured sections list from metadata or fallback to single body section."""
    sections_data = metadata.get("sections")
    sections: list[ArticleSection] = []

    if isinstance(sections_data, list):
        for index, section in enumerate(sections_data, start=1):
            if isinstance(section, dict) and section.get("content"):
                sections.append(
                    ArticleSection(
                        kind=section.get("kind") or f"section_{index}",
                        content=section.get("content", ""),
                    )
                )

    if not sections and body:
        sections.append(ArticleSection(kind="body", content=body))

    return sections


def _build_featured_image_metadata(
    article: Article, metadata: dict[str, Any]
) -> ImageMetadata | None:
    """Construct ImageMetadata for the featured image."""
    featured_meta = metadata.get("featured_image") or metadata.get("featuredImage")

    if isinstance(featured_meta, dict):
        return ImageMetadata(
            id=featured_meta.get("id"),
            path=featured_meta.get("path") or article.featured_image_path,
            url=featured_meta.get("url") or featured_meta.get("source_url"),
            width=_coerce_int(featured_meta.get("width")),
            height=_coerce_int(featured_meta.get("height")),
            file_format=featured_meta.get("format") or featured_meta.get("mime_type"),
            caption=featured_meta.get("caption"),
            source=featured_meta.get("source"),
            photographer=featured_meta.get("photographer"),
        )

    if article.featured_image_path:
        return ImageMetadata(
            path=article.featured_image_path,
            file_format=_guess_format(article.featured_image_path),
        )

    return None


def _build_inline_images(
    article: Article, metadata: dict[str, Any]
) -> list[ImageMetadata]:
    """Construct ImageMetadata entries for inline images."""
    images: list[ImageMetadata] = []
    meta_images = metadata.get("images") or metadata.get("media") or []

    if isinstance(meta_images, list):
        for item in meta_images:
            meta = _to_image_metadata(item)
            if meta:
                images.append(meta)

    if article.additional_images:
        for path in article.additional_images:
            images.append(
                ImageMetadata(
                    path=path,
                    file_format=_guess_format(path),
                )
            )

    return images


def _to_image_metadata(item: Any) -> ImageMetadata | None:
    """Normalize arbitrary image metadata structures."""
    if isinstance(item, dict):
        return ImageMetadata(
            id=item.get("id"),
            path=item.get("path"),
            url=item.get("url") or item.get("source_url"),
            width=_coerce_int(item.get("width")),
            height=_coerce_int(item.get("height")),
            file_format=item.get("format") or item.get("mime_type"),
            caption=item.get("caption"),
            source=item.get("source"),
            photographer=item.get("photographer"),
        )
    if isinstance(item, str):
        return ImageMetadata(path=item, file_format=_guess_format(item))
    return None


def _extract_keywords(metadata: dict[str, Any]) -> list[str]:
    """Collect keywords from metadata for AI context."""
    keywords: list[str] = []
    if isinstance(metadata.get("keywords"), list):
        keywords.extend([value for value in metadata["keywords"] if isinstance(value, str)])
    seo_data = metadata.get("seo")
    if isinstance(seo_data, dict) and isinstance(seo_data.get("keywords"), list):
        keywords.extend(
            [value for value in seo_data["keywords"] if isinstance(value, str)]
        )
    seen: set[str] = set()
    deduped: list[str] = []
    for keyword in keywords:
        if keyword not in seen:
            seen.add(keyword)
            deduped.append(keyword)
    return deduped


def _merge_proofreading_metadata(
    existing: dict[str, Any] | None, result_payload: dict[str, Any]
) -> dict[str, Any]:
    """Merge proofreading result into article metadata."""
    metadata = dict(existing or {})
    metadata["proofreading"] = {
        "statistics": result_payload.get("statistics"),
        "processing_metadata": result_payload.get("processing_metadata"),
        "seo_metadata": result_payload.get("seo_metadata"),
    }
    if result_payload.get("suggested_content"):
        metadata["proofreading"]["suggested_content"] = result_payload[
            "suggested_content"
        ]
    metadata["proofreading"]["issues_snapshot"] = result_payload.get("issues", [])
    return metadata


@lru_cache(maxsize=1)
def _get_proofreading_service() -> ProofreadingAnalysisService:
    """Provide a cached ProofreadingAnalysisService instance."""
    return ProofreadingAnalysisService()


def _guess_format(path: str | None) -> str | None:
    """Guess image format from path suffix."""
    if not path:
        return None
    suffix = Path(path).suffix.lower().lstrip(".")
    return suffix or None


def _coerce_int(value: Any) -> int | None:
    """Convert arbitrary value to int if possible."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
