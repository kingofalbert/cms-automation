"""Worklist API endpoints."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import (
    PaginatedResponse,
    ReviewDecisionsPayload,
    ReviewDecisionsResponse,
    WorklistItemDetailResponse,
    WorklistItemResponse,
    WorklistItemSummary,
    ArticleSummary,
    WorklistStatisticsResponse,
    WorklistStatusHistoryEntry,
    WorklistStatusUpdateRequest,
    WorklistSyncStatusResponse,
    WorklistSyncTriggerResponse,
)
from src.config.database import get_session
from src.config.logging import get_logger
from src.models import Article, ProofreadingDecision, WorklistItem
from src.services.worklist import WorklistService

logger = get_logger(__name__)
router = APIRouter(prefix="/worklist", tags=["Worklist"])

WorklistListResponse = PaginatedResponse[WorklistItemResponse]


@router.get("", response_model=WorklistListResponse)
async def list_worklist_items(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> WorklistListResponse:
    """List worklist items with optional status filtering."""
    service = WorklistService(session)
    try:
        items, total = await service.list_items(
            status=status_filter,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    serialized = [_serialize_item(item) for item in items]
    page = (offset // limit) + 1

    logger.debug(
        "worklist_items_listed",
        count=len(serialized),
        total=total,
        status=status_filter,
    )

    return WorklistListResponse.create(
        items=serialized,
        total=total,
        page=page,
        page_size=limit,
    )


@router.get("/statistics", response_model=WorklistStatisticsResponse)
async def get_worklist_statistics(
    session: AsyncSession = Depends(get_session),
) -> WorklistStatisticsResponse:
    """Return breakdown of worklist statuses."""
    service = WorklistService(session)
    stats = await service.get_statistics()
    total = stats.pop("total", sum(stats.values()))
    return WorklistStatisticsResponse(total=total, breakdown=stats)


@router.get("/sync-status", response_model=WorklistSyncStatusResponse)
async def get_sync_status(
    session: AsyncSession = Depends(get_session),
) -> WorklistSyncStatusResponse:
    """Return latest sync metadata."""
    service = WorklistService(session)
    status_payload = await service.get_sync_status()
    return WorklistSyncStatusResponse(**status_payload)


@router.post("/sync", response_model=WorklistSyncTriggerResponse)
async def trigger_worklist_sync(
    session: AsyncSession = Depends(get_session),
) -> WorklistSyncTriggerResponse:
    """Trigger asynchronous sync with Google Drive."""
    service = WorklistService(session)
    result = await service.trigger_sync()
    return WorklistSyncTriggerResponse(**result)


@router.post("/{item_id}/trigger-proofreading")
async def trigger_item_proofreading(
    item_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Manually trigger proofreading for a worklist item."""
    service = WorklistService(session)
    try:
        result = await service.trigger_proofreading(item_id)
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"],
            )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post("/{item_id}/reparse")
async def trigger_item_reparse(
    item_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Manually trigger re-parsing for a worklist item (useful for testing unified prompt)."""
    service = WorklistService(session)
    try:
        result = await service.trigger_reparse(item_id)
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"],
            )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/{item_id}", response_model=WorklistItemDetailResponse)
async def get_worklist_item_detail(
    item_id: int,
    session: AsyncSession = Depends(get_session),
) -> WorklistItemDetailResponse:
    """Return a single worklist item with full metadata."""
    service = WorklistService(session)
    try:
        item = await service.get_item(item_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    logger.debug("worklist_item_loaded", item_id=item_id)
    return await _serialize_item_detail(item, session)


@router.post("/{item_id}/status", response_model=WorklistItemResponse)
async def update_worklist_status(
    item_id: int,
    payload: WorklistStatusUpdateRequest,
    session: AsyncSession = Depends(get_session),
) -> WorklistItemResponse:
    """Update status of a worklist item."""
    service = WorklistService(session)
    try:
        updated = await service.update_status(
            item_id=item_id,
            status=payload.status,
            note=payload.note,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    logger.info(
        "worklist_status_updated",
        item_id=item_id,
        status=updated.status.value,
    )
    return _serialize_item(updated)


@router.post("/{item_id}/publish", response_model=WorklistItemResponse)
async def publish_worklist_item(
    item_id: int,
    session: AsyncSession = Depends(get_session),
) -> WorklistItemResponse:
    """Placeholder endpoint to initiate publishing from worklist."""
    service = WorklistService(session)
    try:
        updated = await service.update_status(
            item_id=item_id,
            status="ready_to_publish",
            note={"action": "publish", "message": "Publishing triggered from worklist"},
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    logger.info(
        "worklist_publish_triggered",
        item_id=item_id,
        status=updated.status.value,
    )
    return _serialize_item(updated)


@router.post("/{item_id}/review-decisions", response_model=ReviewDecisionsResponse)
async def save_review_decisions(
    item_id: int,
    payload: ReviewDecisionsPayload,
    session: AsyncSession = Depends(get_session),
) -> ReviewDecisionsResponse:
    """Save proofreading review decisions and optionally transition status."""
    from datetime import datetime
    from src.models.proofreading import DecisionType, FeedbackStatus
    from src.models import ArticleStatusHistory, WorklistStatus, ArticleStatus

    # 1. Get worklist item
    item = await session.get(WorklistItem, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worklist item {item_id} not found",
        )

    # 2. Get linked article
    if not item.article_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Worklist item has no linked article",
        )

    article = await session.get(Article, item.article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {item.article_id} not found",
        )

    # 3. Validate issue IDs
    article_issues = article.proofreading_issues or []
    issue_id_map: dict[str, tuple[int, dict[str, Any]]] = {}
    for idx, issue in enumerate(article_issues):
        issue_id = _compute_issue_id(issue, idx)
        issue_id_map[issue_id] = (idx, issue)

    errors = []
    for decision in payload.decisions:
        if decision.issue_id not in issue_id_map:
            errors.append(f"Issue {decision.issue_id} not found in article")

    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": errors},
        )

    # 4. Create ProofreadingDecision records
    saved_count = 0
    article_content = item.content or ""
    for decision_payload in payload.decisions:
        issue_index, issue = issue_id_map[decision_payload.issue_id]
        issue_context = _build_issue_context(
            issue,
            article_content=article_content,
            index=issue_index,
        )

        # Check if decision already exists
        existing = await session.execute(
            select(ProofreadingDecision).where(
                ProofreadingDecision.article_id == article.id,
                ProofreadingDecision.suggestion_id == decision_payload.issue_id,
            )
        )
        existing_decision = existing.scalars().first()

        if existing_decision:
            # Update existing decision
            existing_decision.decision_type = DecisionType(decision_payload.decision_type)
            existing_decision.decision_rationale = decision_payload.decision_rationale
            existing_decision.modified_content = decision_payload.modified_content
            existing_decision.feedback_provided = decision_payload.feedback_provided
            existing_decision.feedback_category = decision_payload.feedback_category
            existing_decision.feedback_notes = decision_payload.feedback_notes
            existing_decision.decided_at = datetime.utcnow()
        else:
            # Create new decision
            new_decision = ProofreadingDecision(
                article_id=article.id,
                suggestion_id=decision_payload.issue_id,
                decision_type=DecisionType(decision_payload.decision_type),
                decision_rationale=decision_payload.decision_rationale,
                modified_content=decision_payload.modified_content,
                original_text=issue_context["original_text"],
                suggested_text=issue_context["suggested_text"],
                rule_id=issue_context["rule_id"],
                rule_category=issue_context["rule_category"],
                issue_position=issue_context["position"],
                feedback_provided=decision_payload.feedback_provided,
                feedback_category=decision_payload.feedback_category,
                feedback_notes=decision_payload.feedback_notes,
                feedback_status=(
                    FeedbackStatus.PENDING
                    if decision_payload.feedback_provided
                    else FeedbackStatus.COMPLETED
                ),
                decided_by=1,  # TODO: Get from current_user
                decided_at=datetime.utcnow(),
            )
            session.add(new_decision)

        saved_count += 1

    # 5. Update statuses if transition_to is specified
    old_worklist_status = item.status.value if hasattr(item.status, "value") else item.status
    old_article_status = article.status.value if hasattr(article.status, "value") else article.status

    if payload.transition_to:
        if payload.transition_to == "ready_to_publish":
            item.mark_status(WorklistStatus.READY_TO_PUBLISH)
            article.status = ArticleStatus.READY_TO_PUBLISH
        elif payload.transition_to == "proofreading":
            item.mark_status(WorklistStatus.PROOFREADING)
            article.status = ArticleStatus.IN_REVIEW
        elif payload.transition_to == "failed":
            item.mark_status(WorklistStatus.FAILED)
            article.status = ArticleStatus.FAILED

        # Create status history
        history = ArticleStatusHistory(
            article_id=article.id,
            old_status=old_article_status,
            new_status=article.status.value,
            changed_by="user:1",  # TODO: Get from current_user
            change_reason=f"review_completed_transition_to_{payload.transition_to}",
            metadata={
                "worklist_id": item.id,
                "decisions_count": saved_count,
                "review_notes": payload.review_notes,
            },
        )
        session.add(history)

    # 6. Add review notes
    if payload.review_notes:
        item.add_note({
            "message": payload.review_notes,
            "level": "info",
            "author": "user:1",  # TODO: Get from current_user
            "created_at": datetime.utcnow().isoformat(),
        })

    # 7. Commit changes
    await session.commit()
    await session.refresh(item)
    await session.refresh(article)

    logger.info(
        "review_decisions_saved",
        item_id=item_id,
        article_id=article.id,
        decisions_count=saved_count,
        transition_to=payload.transition_to,
    )

    return ReviewDecisionsResponse(
        success=True,
        saved_decisions_count=saved_count,
        worklist_item=WorklistItemSummary(
            id=item.id,
            status=item.status.value if hasattr(item.status, "value") else item.status,
            updated_at=item.updated_at.isoformat(),
        ),
        article=ArticleSummary(
            id=article.id,
            status=article.status.value if hasattr(article.status, "value") else article.status,
            updated_at=article.updated_at.isoformat(),
        ),
        errors=[],
    )


def _serialize_item(item: WorklistItem) -> WorklistItemResponse:
    """Convert ORM worklist item to schema."""
    return WorklistItemResponse(
        id=item.id,
        drive_file_id=item.drive_file_id,
        title=item.title,
        status=item.status.value if hasattr(item.status, "value") else item.status,
        author=item.author,
        article_id=item.article_id,
        metadata=item.drive_metadata or {},
        notes=item.notes or [],
        synced_at=item.synced_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


async def _serialize_item_detail(
    item: WorklistItem,
    session: AsyncSession,
) -> WorklistItemDetailResponse:
    """Convert worklist item with related article data to detail schema."""
    base = _serialize_item(item)
    article = getattr(item, "article", None)
    history_entries: list[WorklistStatusHistoryEntry] = []
    if article and getattr(article, "status_history", None):
        for entry in sorted(article.status_history, key=lambda h: h.created_at):
            history_entries.append(
                WorklistStatusHistoryEntry(
                    old_status=entry.old_status,
                    new_status=entry.new_status,
                    changed_by=entry.changed_by,
                    change_reason=entry.change_reason,
                    metadata=entry.change_metadata or {},
                    created_at=entry.created_at,
                )
            )

    # Get proofreading issues and stats
    proofreading_issues = []
    proofreading_stats = None

    if article:
        # Get raw issues from article
        raw_issues = article.proofreading_issues or []

        # Get existing decisions
        stmt = select(ProofreadingDecision).where(
            ProofreadingDecision.article_id == article.id
        )
        result = await session.execute(stmt)
        decisions = {d.suggestion_id: d for d in result.scalars().all()}

        # Enrich issues with decision status
        article_content = item.content or ""
        for idx, issue in enumerate(raw_issues):
            issue_id = _compute_issue_id(issue, idx)
            decision = decisions.get(issue_id)
            normalized_issue = _normalize_issue_for_review(
                issue,
                article_content=article_content,
                index=idx,
                decision_status=(
                    decision.decision_type.value if decision else "pending"
                ),
                decision_id=decision.id if decision else None,
            )
            proofreading_issues.append(normalized_issue)

        # Calculate statistics
        if raw_issues:
            proofreading_stats = _calculate_proofreading_stats(
                proofreading_issues
            )

    # HOTFIX-PARSE-004: Extract parsing fields from linked article
    title_main = None
    title_prefix = None
    title_suffix = None
    author_name = None
    author_line = None
    seo_title = None
    suggested_meta_description = None
    suggested_seo_keywords = None
    parsing_confirmed = False
    parsing_confirmed_at = None

    if article:
        title_main = article.title_main
        title_prefix = article.title_prefix
        title_suffix = article.title_suffix
        author_name = article.author_name
        author_line = article.author_line
        seo_title = article.seo_title if hasattr(article, 'seo_title') else None
        suggested_meta_description = article.suggested_meta_description if hasattr(article, 'suggested_meta_description') else None
        suggested_seo_keywords = article.suggested_seo_keywords if hasattr(article, 'suggested_seo_keywords') else None
        parsing_confirmed = article.parsing_confirmed if hasattr(article, 'parsing_confirmed') else False
        parsing_confirmed_at = article.parsing_confirmed_at if hasattr(article, 'parsing_confirmed_at') else None

        # Extract article images
        article_images = []
        if hasattr(article, 'article_images'):
            from src.api.schemas.article import ArticleImageResponse
            for img in article.article_images:
                article_images.append(ArticleImageResponse(
                    id=img.id,
                    article_id=img.article_id,
                    preview_path=img.preview_path,
                    source_path=img.source_path,
                    source_url=img.source_url,
                    caption=img.caption,
                    alt_text=img.alt_text,
                    description=img.description,
                    position=img.position,
                    # Phase 13: Featured image detection fields
                    is_featured=img.is_featured if hasattr(img, 'is_featured') else False,
                    image_type=img.image_type if hasattr(img, 'image_type') else "content",
                    detection_method=img.detection_method if hasattr(img, 'detection_method') else None,
                    image_metadata=img.image_metadata or {},
                    created_at=img.created_at,
                    updated_at=img.updated_at,
                ))
    else:
        article_images = []

    # Get article_metadata for FAQ state persistence
    article_metadata = {}
    if article and hasattr(article, 'article_metadata'):
        article_metadata = article.article_metadata or {}

    # Phase 14: Get extracted FAQs from article
    extracted_faqs = None
    extracted_faqs_detection_method = None
    if article and hasattr(article, 'extracted_faqs'):
        extracted_faqs = article.extracted_faqs
        extracted_faqs_detection_method = article.extracted_faqs_detection_method

    # Phase 15: Get category fields from article for auto-save persistence
    primary_category = None
    secondary_categories = []
    if article:
        primary_category = article.primary_category if hasattr(article, 'primary_category') else None
        secondary_categories = article.secondary_categories if hasattr(article, 'secondary_categories') else []

    return WorklistItemDetailResponse(
        **base.model_dump(),
        content=item.content,
        tags=item.tags or [],
        categories=item.categories or [],
        meta_description=item.meta_description,
        seo_keywords=item.seo_keywords or [],
        article_status=article.status.value if article and article.status else None,
        article_status_history=history_entries,
        drive_metadata=item.drive_metadata or {},
        proofreading_issues=proofreading_issues,
        proofreading_stats=proofreading_stats,
        # Phase 7: Parsing fields from article
        title_main=title_main,
        title_prefix=title_prefix,
        title_suffix=title_suffix,
        author_name=author_name,
        author_line=author_line,
        seo_title=seo_title,
        suggested_meta_description=suggested_meta_description,
        suggested_seo_keywords=suggested_seo_keywords,
        parsing_confirmed=parsing_confirmed,
        parsing_confirmed_at=parsing_confirmed_at,
        # Phase 7: Article images
        article_images=article_images,
        # FAQ state persistence: include article_metadata with faq_suggestions
        article_metadata=article_metadata,
        # Phase 14: Extracted FAQs from original article
        extracted_faqs=extracted_faqs,
        extracted_faqs_detection_method=extracted_faqs_detection_method,
        # Phase 15: Category fields for auto-save persistence
        primary_category=primary_category,
        secondary_categories=secondary_categories or [],
    )


def _calculate_proofreading_stats(issues: list[dict]) -> dict[str, int]:
    """Calculate statistics from proofreading issues."""
    stats = {
        "total_issues": len(issues),
        "critical_count": 0,
        "warning_count": 0,
        "info_count": 0,
        "pending_count": 0,
        "accepted_count": 0,
        "rejected_count": 0,
        "modified_count": 0,
        "ai_issues_count": 0,
        "deterministic_issues_count": 0,
    }

    for issue in issues:
        # Count by severity
        severity = issue.get("severity", "").lower()
        if severity == "critical":
            stats["critical_count"] += 1
        elif severity == "warning":
            stats["warning_count"] += 1
        elif severity == "info":
            stats["info_count"] += 1

        # Count by decision status
        decision_status = issue.get("decision_status", "pending")
        if decision_status == "pending":
            stats["pending_count"] += 1
        elif decision_status == "accepted":
            stats["accepted_count"] += 1
        elif decision_status == "rejected":
            stats["rejected_count"] += 1
        elif decision_status == "modified":
            stats["modified_count"] += 1

        # Count by engine
        engine = issue.get("engine", "").lower()
        if engine == "ai":
            stats["ai_issues_count"] += 1
        elif engine == "deterministic":
            stats["deterministic_issues_count"] += 1

    return stats


def _normalize_issue_for_review(
    issue: dict[str, Any],
    *,
    article_content: str,
    index: int,
    decision_status: str,
    decision_id: int | None,
) -> dict[str, Any]:
    """Normalize stored issue payload into UI-friendly format."""
    context = _build_issue_context(
        issue,
        article_content=article_content,
        index=index,
    )
    context["decision_status"] = decision_status or "pending"
    context["decision_id"] = decision_id
    return context


def _build_issue_context(
    issue: dict[str, Any],
    *,
    article_content: str,
    index: int,
) -> dict[str, Any]:
    """Derive consistent identifiers and text snippets for a proofreading issue."""
    position, start, end = _compute_position(issue)

    # Priority for original_text:
    # 1. Explicitly stored original_text
    # 2. Extract from article content using position
    # 3. Fall back to evidence
    # 4. Fall back to message (issue description)
    original_text = issue.get("original_text")
    if (not original_text) and article_content and end > start:
        original_text = _safe_slice(article_content, start, end)
    if not original_text:
        original_text = issue.get("evidence") or ""
    # If still empty, use message as display text (but mark it differently)
    display_original = original_text if original_text else issue.get("message", "")

    # Priority for suggested_text:
    # 1. Explicitly stored suggested_text
    # 2. suggestion field
    # 3. Same as original (no change suggested)
    suggested_text = (
        issue.get("suggested_text")
        or issue.get("suggestion")
        or ""
    )
    # If no suggestion, indicate same as original
    display_suggested = suggested_text if suggested_text else display_original

    explanation = issue.get("explanation") or issue.get("message") or ""
    explanation_detail = issue.get("explanation_detail") or issue.get("evidence")

    context = {
        "id": _compute_issue_id(issue, index),
        "rule_id": issue.get("rule_id") or f"rule_{index}",
        "rule_category": (
            issue.get("rule_category")
            or issue.get("category")
            or issue.get("subcategory")
            or (issue.get("rule_id", "U")[:1] or "U")
        ),
        "severity": _normalize_severity(issue.get("severity")),
        "engine": _derive_engine(issue),
        "position": position,
        "original_text": display_original,
        "suggested_text": display_suggested,
        "explanation": explanation,
        "explanation_detail": explanation_detail,
        "confidence": issue.get("confidence"),
        "tags": issue.get("tags") or [],
    }
    return context


def _compute_issue_id(issue: dict[str, Any], index: int) -> str:
    """Return an existing issue id or derive a stable hash-based identifier."""
    existing_id = issue.get("id")
    if existing_id:
        return str(existing_id)

    fingerprint = json.dumps(
        {
            "rule_id": issue.get("rule_id"),
            "message": issue.get("message"),
            "suggestion": issue.get("suggestion"),
            "location": issue.get("location"),
            "subcategory": issue.get("subcategory"),
        },
        sort_keys=True,
        default=str,
    )
    digest = hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()
    return f"sug_{digest[:12]}_{index}"


def _compute_position(issue: dict[str, Any]) -> tuple[dict[str, Any], int, int]:
    """Determine safe start/end offsets for an issue."""
    raw_position = issue.get("position") or {}
    location = issue.get("location") or {}

    start = _coerce_int(raw_position.get("start"))
    end = _coerce_int(raw_position.get("end"))

    if start is None:
        start = _coerce_int(location.get("start")) or _coerce_int(location.get("offset"))
    if end is None:
        end = _coerce_int(location.get("end"))
    if start is not None and (end is None or end < start):
        length = _coerce_int(raw_position.get("length")) or _coerce_int(
            location.get("length")
        )
        if length is not None:
            end = start + length

    if start is None:
        start = 0
    if end is None or end < start:
        end = start

    position = {
        "start": start,
        "end": end,
        "section": raw_position.get("section")
        or location.get("section")
        or location.get("tag"),
        "line": raw_position.get("line") or location.get("line"),
        "column": raw_position.get("column") or location.get("column"),
    }
    return position, start, end


def _safe_slice(content: str, start: int, end: int) -> str:
    """Return substring within bounds."""
    if not content:
        return ""
    length = len(content)
    start_idx = max(0, min(length, start))
    end_idx = max(start_idx, min(length, end))
    return content[start_idx:end_idx]


def _coerce_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_severity(value: str | None) -> str:
    if not value:
        return "info"
    value = value.lower()
    if value in {"critical", "error", "blocker"}:
        return "critical"
    if value in {"warning", "warn"}:
        return "warning"
    return "info"


def _derive_engine(issue: dict[str, Any]) -> str:
    engine = issue.get("engine")
    if engine:
        return str(engine).lower()
    source = str(issue.get("source") or "").lower()
    if source in {"ai", "merged"}:
        return "ai"
    return "deterministic"
