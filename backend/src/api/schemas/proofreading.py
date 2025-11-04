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
