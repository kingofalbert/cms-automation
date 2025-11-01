"""API schema for proofreading analysis responses."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProofreadingIssueSchema(BaseModel):
    """Schema representing a single proofreading issue."""

    rule_id: str = Field(..., description="Unique rule identifier (e.g. A1-001)")
    category: str = Field(..., description="Rule category (A-F)")
    subcategory: Optional[str] = Field(default=None, description="Rule subcategory, e.g. A1")
    message: str = Field(..., description="Human readable description of the issue")
    suggestion: Optional[str] = Field(default=None, description="Optional fix recommendation")
    severity: str = Field(..., description="Issue severity (info|warning|error|critical)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    can_auto_fix: bool = Field(default=False)
    blocks_publish: bool = Field(default=False)
    source: str = Field(..., description="Origin of issue: ai/script/merged")
    attributed_by: Optional[str] = Field(default=None, description="Component identifiers that raised issue")
    location: Optional[Dict[str, Any]] = Field(default=None, description="Pointer to affected content")
    evidence: Optional[str] = Field(default=None, description="Supporting excerpt or metadata")


class ProofreadingStatisticsSchema(BaseModel):
    """Aggregated stats for proofreading result."""

    total_issues: int = 0
    ai_issue_count: int = 0
    script_issue_count: int = 0
    blocking_issue_count: int = 0
    categories: Dict[str, int] = Field(default_factory=dict)
    source_breakdown: Dict[str, int] = Field(default_factory=dict)


class ProcessingMetadataSchema(BaseModel):
    """Metadata about the AI/script processing run."""

    ai_model: Optional[str] = Field(default=None)
    ai_latency_ms: Optional[int] = Field(default=None)
    prompt_tokens: Optional[int] = Field(default=None)
    completion_tokens: Optional[int] = Field(default=None)
    total_tokens: Optional[int] = Field(default=None)
    prompt_hash: Optional[str] = Field(default=None)
    rule_manifest_version: Optional[str] = Field(default=None)
    script_engine_version: Optional[str] = Field(default=None)
    notes: Dict[str, Any] = Field(default_factory=dict)


class ProofreadingResponse(BaseModel):
    """API response schema for combined AI + deterministic proofreading."""

    article_id: Optional[int] = Field(default=None)
    issues: List[ProofreadingIssueSchema] = Field(default_factory=list)
    statistics: ProofreadingStatisticsSchema = Field(
        default_factory=ProofreadingStatisticsSchema
    )
    suggested_content: Optional[str] = Field(
        default=None, description="AI suggested body text if provided"
    )
    seo_metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="SEO metadata bundle (title, description, keywords)"
    )
    processing_metadata: ProcessingMetadataSchema = Field(
        default_factory=ProcessingMetadataSchema
    )
