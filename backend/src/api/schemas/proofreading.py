"""API schema for proofreading analysis responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProofreadingIssueSchema(BaseModel):
    """Schema representing a single proofreading issue."""

    rule_id: str = Field(..., description="Unique rule identifier (e.g. A1-001)")
    category: str = Field(..., description="Rule category (A-F)")
    subcategory: str | None = Field(default=None, description="Rule subcategory, e.g. A1")
    message: str = Field(..., description="Human readable description of the issue")
    suggestion: str | None = Field(default=None, description="Optional fix recommendation")
    severity: str = Field(..., description="Issue severity (info|warning|error|critical)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    can_auto_fix: bool = Field(default=False)
    blocks_publish: bool = Field(default=False)
    source: str = Field(..., description="Origin of issue: ai/script/merged")
    attributed_by: str | None = Field(default=None, description="Component identifiers that raised issue")
    location: dict[str, Any] | None = Field(default=None, description="Pointer to affected content")
    evidence: str | None = Field(default=None, description="Supporting excerpt or metadata")


class ProofreadingStatisticsSchema(BaseModel):
    """Aggregated stats for proofreading result."""

    total_issues: int = 0
    ai_issue_count: int = 0
    script_issue_count: int = 0
    blocking_issue_count: int = 0
    categories: dict[str, int] = Field(default_factory=dict)
    source_breakdown: dict[str, int] = Field(default_factory=dict)


class ProcessingMetadataSchema(BaseModel):
    """Metadata about the AI/script processing run."""

    ai_model: str | None = Field(default=None)
    ai_latency_ms: int | None = Field(default=None)
    prompt_tokens: int | None = Field(default=None)
    completion_tokens: int | None = Field(default=None)
    total_tokens: int | None = Field(default=None)
    prompt_hash: str | None = Field(default=None)
    rule_manifest_version: str | None = Field(default=None)
    script_engine_version: str | None = Field(default=None)
    notes: dict[str, Any] = Field(default_factory=dict)


class ProofreadingResponse(BaseModel):
    """API response schema for combined AI + deterministic proofreading."""

    article_id: int | None = Field(default=None)
    issues: list[ProofreadingIssueSchema] = Field(default_factory=list)
    statistics: ProofreadingStatisticsSchema = Field(
        default_factory=ProofreadingStatisticsSchema
    )
    suggested_content: str | None = Field(
        default=None, description="AI suggested body text if provided"
    )
    seo_metadata: dict[str, Any] | None = Field(
        default=None, description="SEO metadata bundle (title, description, keywords)"
    )
    processing_metadata: ProcessingMetadataSchema = Field(
        default_factory=ProcessingMetadataSchema
    )


# Proofreading Review UI Schemas (Feature 003)


class ProofreadingPosition(BaseModel):
    """Position information for a proofreading issue."""

    start: int = Field(..., description="Start character offset")
    end: int = Field(..., description="End character offset")
    line: int | None = Field(default=None, description="Line number")
    column: int | None = Field(default=None, description="Column number")
    section: str | None = Field(default=None, description="Section identifier")


class ProofreadingIssueDetail(BaseModel):
    """Detailed proofreading issue for review UI."""

    id: str = Field(..., description="Issue identifier")
    rule_id: str = Field(..., description="Rule that generated this issue")
    rule_category: str = Field(..., description="Rule category")
    severity: str = Field(..., description="Issue severity (critical|warning|info)")
    engine: str = Field(..., description="Engine type (ai|deterministic)")

    position: dict[str, Any] = Field(..., description="Position in text")

    original_text: str = Field(..., description="Original text")
    suggested_text: str = Field(..., description="Suggested replacement")
    explanation: str = Field(..., description="Short explanation")
    explanation_detail: str | None = Field(default=None, description="Detailed explanation")

    confidence: float | None = Field(default=None, description="AI confidence (0-1)")
    decision_status: str = Field(..., description="Decision status (pending|accepted|rejected|modified)")
    decision_id: int | None = Field(default=None, description="Decision record ID")
    tags: list[str] = Field(default_factory=list, description="Issue tags")


class ProofreadingReviewStats(BaseModel):
    """Statistics about proofreading issues for review UI."""

    total_issues: int = Field(..., ge=0)
    critical_count: int = Field(..., ge=0)
    warning_count: int = Field(..., ge=0)
    info_count: int = Field(..., ge=0)
    pending_count: int = Field(..., ge=0)
    accepted_count: int = Field(..., ge=0)
    rejected_count: int = Field(..., ge=0)
    modified_count: int = Field(..., ge=0)
    ai_issues_count: int = Field(..., ge=0)
    deterministic_issues_count: int = Field(..., ge=0)


class DecisionPayload(BaseModel):
    """Payload for a single proofreading decision."""

    issue_id: str = Field(..., description="Issue identifier")
    decision_type: str = Field(..., description="Decision type (accepted|rejected|modified)")
    decision_rationale: str | None = Field(
        default=None, max_length=1000, description="Rationale for decision"
    )
    modified_content: str | None = Field(default=None, description="Modified content")
    feedback_provided: bool = Field(default=False, description="Whether feedback is provided")
    feedback_category: str | None = Field(default=None, description="Feedback category")
    feedback_notes: str | None = Field(
        default=None, max_length=2000, description="Feedback notes"
    )


class ReviewDecisionsPayload(BaseModel):
    """Request payload for saving review decisions."""

    decisions: list[DecisionPayload] = Field(..., description="List of decisions")
    review_notes: str | None = Field(
        default=None, max_length=5000, description="Overall review notes"
    )
    transition_to: str | None = Field(
        default=None, description="Target status (ready_to_publish|proofreading|failed)"
    )


class WorklistItemSummary(BaseModel):
    """Summary of worklist item after review."""

    id: int
    status: str
    updated_at: str


class ArticleSummary(BaseModel):
    """Summary of article after review."""

    id: int
    status: str
    updated_at: str


class ReviewDecisionsResponse(BaseModel):
    """Response after saving review decisions."""

    success: bool
    saved_decisions_count: int
    worklist_item: WorklistItemSummary
    article: ArticleSummary
    errors: list[str] = Field(default_factory=list)


class BatchDecisionsPayload(BaseModel):
    """Payload for batch decisions."""

    issue_ids: list[str] = Field(..., min_length=1, description="List of issue IDs")
    decision_type: str = Field(..., description="Decision type (accepted|rejected)")
    rationale: str | None = Field(default=None, max_length=1000, description="Rationale")


class SavedDecisionSummary(BaseModel):
    """Summary of a saved decision."""

    issue_id: str
    decision_id: int
    decision_type: str


class BatchDecisionsResponse(BaseModel):
    """Response for batch decisions."""

    success: bool
    processed_count: int
    failed: list[str] = Field(default_factory=list)
    saved_decisions: list[SavedDecisionSummary] = Field(default_factory=list)
