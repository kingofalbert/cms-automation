"""Article API routes."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes, selectinload

from src.api.schemas import ProofreadingResponse
from src.api.schemas.article import (
    ArticleListResponse,
    ArticleResponse,
    ArticleReviewResponse,
    ContentComparison,
    MetaComparison,
    SEOComparison,
    TagsComparison,
    SuggestedTag,
    FAQProposal,
    ParagraphSuggestion,
    ProofreadingDecisionDetail,
    RelatedArticleResponse,
)
from src.config.database import get_session
from src.config.logging import get_logger
from src.models import Article
from src.models.article_image import ArticleImage
from src.models.proofreading import ProofreadingDecision
from src.models.seo_suggestions import SEOSuggestion
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


@router.post("/{article_id}/reparse", response_model=ArticleResponse)
async def reparse_article(
    article_id: int,
    session: AsyncSession = Depends(get_session),
) -> Article:
    """Re-parse an article from Google Drive using the latest parser."""
    from src.config.settings import get_settings
    from src.services.storage import create_google_drive_storage
    from src.services.parser.article_parser import ArticleParserService

    article = await _fetch_article(session, article_id)
    settings = get_settings()

    # Get Google Drive file ID from metadata
    metadata = article.article_metadata or {}
    file_id = metadata.get("id") or metadata.get("google_drive", {}).get("file_id")

    if not file_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Article does not have Google Drive file ID in metadata",
        )

    logger.info(f"Re-parsing article {article_id} from Drive file {file_id}")

    try:
        # Download content from Google Drive
        storage = await create_google_drive_storage()

        # Export Google Doc as HTML (preserves structure and images)
        request = storage.service.files().export(fileId=file_id, mimeType="text/html")
        raw_html_bytes = request.execute()
        raw_html = raw_html_bytes.decode("utf-8", errors="ignore") if isinstance(raw_html_bytes, bytes) else raw_html_bytes

        # Parse with latest parser (Claude Sonnet 4.5) using unified prompt
        # for primary_category classification and focus_keyword extraction
        parser = ArticleParserService(
            use_ai=True,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            use_unified_prompt=True,
        )
        result = parser.parse_document(raw_html)

        if not result.success:
            error_msg = "; ".join([e.error_message for e in result.errors])
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Parsing failed: {error_msg}",
            )

        # Update article with new parsing results
        parsed = result.parsed_article
        article.title_prefix = parsed.title_prefix
        # HOTFIX-PARSE-005: Use Google Drive title (article.title) as primary title_main
        # The AI parser often confuses author line with title, so we prioritize
        # the title from Google Drive file name which is more reliable
        article.title_main = article.title or parsed.title_main
        article.title_suffix = parsed.title_suffix
        article.seo_title = parsed.seo_title
        article.seo_title_extracted = parsed.seo_title_extracted
        article.seo_title_source = parsed.seo_title_source
        article.author_line = parsed.author_line
        article.author_name = parsed.author_name
        # HOTFIX-PARSE-004: Save body_html to fix "0 字符" issue in UI
        # HOTFIX-PARSE-006: Clean body_html by removing author line if present
        clean_body_html = _clean_body_html(parsed.body_html, parsed.author_line)
        article.body = clean_body_html
        article.body_html = clean_body_html
        article.meta_description = parsed.meta_description
        article.seo_keywords = parsed.seo_keywords
        article.tags = parsed.tags
        # Phase 10: WordPress taxonomy fields
        article.primary_category = parsed.primary_category
        article.focus_keyword = parsed.focus_keyword

        # Update metadata with new parsing info
        article.article_metadata = article.article_metadata or {}
        article.article_metadata["parsing"] = {
            "method": parsed.parsing_method,
            "confidence": parsed.parsing_confidence,
            "parsed_at": result.metadata.get("timestamp", ""),
            "model": result.metadata.get("model", ""),
        }
        article.article_metadata["images"] = [
            {
                "position": img.position,
                "source_url": img.source_url,
                "caption": img.caption,
            }
            for img in parsed.images
        ]

        # Mark JSON field as modified so SQLAlchemy knows to update it
        attributes.flag_modified(article, "article_metadata")

        # Phase 10: Save images to article_images table
        # First, delete existing images for this article (reparse = fresh start)
        await session.execute(
            delete(ArticleImage).where(ArticleImage.article_id == article_id)
        )

        # Expire the article's article_images relationship to clear references to deleted objects
        # This is critical to avoid "Instance has been deleted" errors
        session.expire(article, ["article_images"])

        # Create new ArticleImage records for each parsed image
        for img in parsed.images:
            if img.source_url:  # Only save images with source URLs
                article_image = ArticleImage(
                    article_id=article_id,
                    source_url=img.source_url,
                    caption=img.caption,
                    alt_text=img.caption,  # Use caption as alt text for accessibility
                    position=img.position,
                )
                session.add(article_image)

        logger.info(
            f"Saved {len(parsed.images)} images to article_images table for article {article_id}"
        )

        await session.commit()

        # Reload article with images relationship for response
        result = await session.execute(
            select(Article)
            .where(Article.id == article_id)
            .options(selectinload(Article.article_images))
        )
        article = result.scalar_one()

        logger.info(f"Successfully re-parsed article {article_id} with {parsed.parsing_method}")
        return article

    except Exception as exc:
        logger.error(
            "reparse_failed",
            article_id=article_id,
            file_id=file_id,
            error=str(exc),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Re-parse failed: {str(exc)}",
        ) from exc


async def _fetch_article(session: AsyncSession, article_id: int) -> Article:
    """Fetch article or raise 404.

    Eagerly loads article_images relationship for API responses.
    """
    result = await session.execute(
        select(Article)
        .where(Article.id == article_id)
        .options(selectinload(Article.article_images))
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found",
        )
    return article


def _clean_body_html(body_html: str | None, author_line: str | None) -> str:
    """Clean body_html by removing author line, image metadata, and trailing keywords.

    HOTFIX-PARSE-006: Ensures body_html contains only the article content,
    without metadata that should be displayed separately.

    Args:
        body_html: Raw body HTML from parsing
        author_line: Extracted author line to remove

    Returns:
        Cleaned body HTML
    """
    if not body_html:
        return ""

    soup = BeautifulSoup(body_html, "html.parser")
    paragraphs = soup.find_all("p")

    # Track which paragraphs to remove
    paragraphs_to_remove = []

    for i, p in enumerate(paragraphs):
        text = p.get_text(strip=True)

        # Remove author line paragraph (usually first paragraph)
        if author_line and text and author_line.strip() in text:
            paragraphs_to_remove.append(p)
            logger.debug(f"Removing author line paragraph: {text[:50]}...")
            continue

        # Remove image metadata paragraphs (圖片, 圖片連結)
        if text and (
            text.startswith("圖片：") or
            text.startswith("圖片:") or
            text.startswith("圖片連結：") or
            text.startswith("圖片連結:") or
            text.startswith("圖說：") or
            text.startswith("圖說:")
        ):
            paragraphs_to_remove.append(p)
            logger.debug(f"Removing image metadata paragraph: {text[:50]}...")
            continue

        # Remove keyword/tag lines at the end (check last 5 paragraphs)
        if i >= len(paragraphs) - 5:
            # Detect keyword lines: comma/space separated short terms
            # Pattern: multiple short Chinese phrases separated by , or 、
            if text and len(text) < 300:
                # Check if it looks like a keyword list
                parts = re.split(r"[,，、\s]+", text)
                if len(parts) >= 5:  # At least 5 keywords
                    # Check if all parts are short (keywords are usually < 15 chars)
                    if all(len(part.strip()) < 15 for part in parts if part.strip()):
                        paragraphs_to_remove.append(p)
                        logger.debug(f"Removing keyword paragraph: {text[:50]}...")
                        continue

    # Remove marked paragraphs
    for p in paragraphs_to_remove:
        p.decompose()

    # Return cleaned HTML
    result = str(soup)
    logger.info(
        "body_html_cleaned",
        original_length=len(body_html),
        cleaned_length=len(result),
        paragraphs_removed=len(paragraphs_to_remove),
    )
    return result


def _build_article_payload(article: Article) -> ArticlePayload:
    """Convert Article ORM object to Proofreading service payload.

    IMPORTANT: For proofreading, we use body_html (cleaned body content) instead
    of the raw body. This ensures:
    1. Only the article body is proofread (not title, author, or SEO metadata)
    2. Rules are applied to the correct content scope
    3. Avoids false positives from title/author sections

    Backward compatibility: Falls back to article.body if body_html is not available.
    """
    metadata = dict(article.article_metadata or {})

    # Use cleaned body_html for proofreading (preferred)
    # Falls back to article.body for backward compatibility with older articles
    proofreading_content = article.body_html or article.body or ""

    # Build sections from the cleaned content
    sections = _extract_article_sections(metadata, proofreading_content)
    featured_image = _build_featured_image_metadata(article, metadata)
    images = _build_inline_images(article, metadata)
    keywords = _extract_keywords(metadata)

    # HTML content for rendering (may include more than just body)
    html_content = (
        metadata.get("rendered_html")
        or metadata.get("html")
        or metadata.get("body_html")
        or article.body_html
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
        original_content=proofreading_content,  # Use cleaned body for proofreading
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


@router.post("/{article_id}/refresh-related-articles", response_model=ArticleResponse)
async def refresh_related_articles(
    article_id: int,
    session: AsyncSession = Depends(get_session),
) -> Article:
    """Refresh related articles for an existing article without full re-parsing.

    This endpoint calls the Supabase match-internal-links Edge Function to find
    semantically related articles based on the article's title and SEO keywords.

    Phase 12: Internal Link Integration
    """
    from src.services.internal_links import get_internal_link_service

    article = await _fetch_article(session, article_id)

    # Get title and keywords for matching
    title = article.title_main or article.title or ""
    keywords = article.seo_keywords or []

    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Article does not have a title for matching",
        )

    logger.info(
        f"Refreshing related articles for article {article_id}: "
        f"title='{title[:50]}...', keywords={len(keywords)}"
    )

    try:
        # Call internal link service
        service = get_internal_link_service()
        result = await service.match_related_articles(
            title=title,
            keywords=keywords,
            limit=5,
        )

        if not result.success:
            logger.warning(
                f"Related article matching failed for article {article_id}: {result.error}"
            )
            # Don't fail the request, just log and continue with empty list
            article.related_articles = []
        else:
            # Store matches as list of dicts
            article.related_articles = [match.model_dump() for match in result.matches]
            logger.info(
                f"Found {len(result.matches)} related articles for article {article_id}"
            )

        # Mark JSON field as modified
        attributes.flag_modified(article, "related_articles")

        await session.commit()

        # Reload article with images relationship
        result_query = await session.execute(
            select(Article)
            .where(Article.id == article_id)
            .options(selectinload(Article.article_images))
        )
        article = result_query.scalar_one()

        return article

    except Exception as exc:
        logger.error(
            "refresh_related_articles_failed",
            article_id=article_id,
            error=str(exc),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh related articles: {str(exc)}",
        ) from exc


@router.get("/{article_id}/review-data", response_model=ArticleReviewResponse)
async def get_article_review_data(
    article_id: int,
    session: AsyncSession = Depends(get_session),
) -> ArticleReviewResponse:
    """
    Get complete article review data for ProofreadingReviewPage.

    Returns:
        - Original vs suggested content comparison
        - Meta description comparison
        - SEO keywords comparison
        - FAQ proposals
        - Paragraph suggestions
        - Proofreading issues
        - Existing proofreading decisions (hydrated from database)
    """
    # Fetch article
    article = await _fetch_article(session, article_id)

    # Fetch existing proofreading decisions
    decisions_result = await session.execute(
        select(ProofreadingDecision)
        .where(ProofreadingDecision.article_id == article_id)
        .order_by(ProofreadingDecision.created_at.desc())
    )
    decisions = decisions_result.scalars().all()

    # Build content comparison
    content = ContentComparison(
        original=article.body or "",
        suggested=article.suggested_content,
        changes=article.suggested_content_changes,
    )

    # Build meta comparison
    original_meta = article.article_metadata.get("meta_description") if article.article_metadata else None
    meta = MetaComparison(
        original=original_meta,
        suggested=article.suggested_meta_description,
        reasoning=article.suggested_meta_reasoning,
        score=article.suggested_meta_score,
        length_original=len(original_meta) if original_meta else 0,
        length_suggested=len(article.suggested_meta_description) if article.suggested_meta_description else 0,
    )

    # Build SEO comparison
    original_keywords = []
    if article.article_metadata:
        seo_data = article.article_metadata.get("seo", {})
        if isinstance(seo_data, dict):
            original_keywords = seo_data.get("keywords", [])

    seo = SEOComparison(
        original_keywords=original_keywords if isinstance(original_keywords, list) else [],
        suggested_keywords=article.suggested_seo_keywords,
        reasoning=article.suggested_keywords_reasoning,
        score=article.suggested_keywords_score,
    )

    # Parse FAQ proposals
    faq_proposals = []
    if article.faq_schema_proposals:
        if isinstance(article.faq_schema_proposals, list):
            for proposal_data in article.faq_schema_proposals:
                if isinstance(proposal_data, dict):
                    faq_proposals.append(FAQProposal(
                        questions=proposal_data.get("questions", []),
                        schema_type=proposal_data.get("schema_type", "FAQPage"),
                        score=proposal_data.get("score"),
                    ))

    # Parse paragraph suggestions
    paragraph_suggestions = []
    if article.paragraph_suggestions:
        if isinstance(article.paragraph_suggestions, list):
            for idx, suggestion_data in enumerate(article.paragraph_suggestions):
                if isinstance(suggestion_data, dict):
                    paragraph_suggestions.append(ParagraphSuggestion(
                        paragraph_index=suggestion_data.get("paragraph_index", idx),
                        original_text=suggestion_data.get("original_text", ""),
                        suggested_text=suggestion_data.get("suggested_text", ""),
                        reasoning=suggestion_data.get("reasoning", ""),
                        improvement_type=suggestion_data.get("improvement_type", "rewrite"),
                    ))

    # Build existing decisions list
    existing_decisions = [
        ProofreadingDecisionDetail(
            issue_id=d.issue_id,
            decision_type=d.decision_type,
            rationale=d.rationale,
            modified_content=d.modified_content,
            reviewer=d.reviewer or "unknown",
            decided_at=d.created_at,
        )
        for d in decisions
    ]

    # Fetch SEO suggestions for tags data
    seo_suggestion_result = await session.execute(
        select(SEOSuggestion)
        .where(SEOSuggestion.article_id == article_id)
        .order_by(SEOSuggestion.generated_at.desc())
        .limit(1)
    )
    seo_suggestion = seo_suggestion_result.scalar_one_or_none()

    # Build tags comparison
    tags_comparison = None
    if article.tags or seo_suggestion:
        suggested_tags = None
        if seo_suggestion and seo_suggestion.suggested_tags:
            # Convert raw suggested_tags dict to SuggestedTag objects
            raw_tags = seo_suggestion.suggested_tags
            if isinstance(raw_tags, list):
                suggested_tags = [
                    SuggestedTag(
                        tag=t.get("tag", ""),
                        relevance=t.get("relevance", 0.5),
                        type=t.get("type", "secondary"),
                        existing=t.get("existing"),
                        article_count=t.get("article_count"),
                    )
                    for t in raw_tags
                    if isinstance(t, dict)
                ]

        tags_comparison = TagsComparison(
            original_tags=article.tags or [],
            suggested_tags=suggested_tags,
            tag_strategy=seo_suggestion.tag_strategy if seo_suggestion else None,
        )

    # Phase 12: Build related articles list
    related_articles = []
    if article.related_articles:
        for ra in article.related_articles:
            if isinstance(ra, dict):
                related_articles.append(RelatedArticleResponse(
                    article_id=ra.get("article_id", ""),
                    title=ra.get("title", ""),
                    title_main=ra.get("title_main"),
                    url=ra.get("url", ""),
                    excerpt=ra.get("excerpt"),
                    similarity=ra.get("similarity", 0.0),
                    match_type=ra.get("match_type", "keyword"),
                    ai_keywords=ra.get("ai_keywords", []),
                ))

    # HOTFIX: Compute stable issue IDs for proofreading_issues
    # This ensures consistency with worklist_routes._compute_issue_id
    raw_issues = article.proofreading_issues or []
    processed_issues = []
    for idx, issue in enumerate(raw_issues):
        if isinstance(issue, dict):
            issue_copy = dict(issue)
            # If issue doesn't have an 'id', compute one using the same algorithm as worklist_routes
            if not issue_copy.get("id"):
                import hashlib
                import json as json_module
                fingerprint = json_module.dumps(
                    {
                        "rule_id": issue_copy.get("rule_id"),
                        "message": issue_copy.get("message"),
                        "suggestion": issue_copy.get("suggestion"),
                        "location": issue_copy.get("location"),
                        "subcategory": issue_copy.get("subcategory"),
                    },
                    sort_keys=True,
                    default=str,
                )
                digest = hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()
                issue_copy["id"] = f"sug_{digest[:12]}_{idx}"
            processed_issues.append(issue_copy)
        else:
            processed_issues.append(issue)

    return ArticleReviewResponse(
        id=article.id,
        title=article.title,
        status=article.status,
        content=content,
        meta=meta,
        seo=seo,
        tags=tags_comparison,
        faq_proposals=faq_proposals,
        paragraph_suggestions=paragraph_suggestions,
        proofreading_issues=processed_issues,
        existing_decisions=existing_decisions,
        related_articles=related_articles,
        ai_model_used=article.ai_model_used,
        suggested_generated_at=article.suggested_generated_at,
        generation_cost=float(article.generation_cost) if article.generation_cost else None,
        created_at=article.created_at,
        updated_at=article.updated_at,
    )
