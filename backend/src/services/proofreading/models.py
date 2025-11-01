"""Shared models for proofreading orchestration."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RuleSource(str, Enum):
    """Origin of a proofreading rule hit."""

    AI = "ai"
    SCRIPT = "script"
    MERGED = "merged"


class ImageMetadata(BaseModel):
    """Metadata for images referenced in an article."""

    id: Optional[str] = Field(
        default=None, description="Unique identifier for the image (CMS/storage id)"
    )
    path: Optional[str] = Field(
        default=None, description="Filesystem or object storage path"
    )
    url: Optional[str] = Field(default=None, description="Remote URL if available")
    width: Optional[int] = Field(
        default=None, description="Pixel width (used for F 类规则)"
    )
    height: Optional[int] = Field(
        default=None, description="Pixel height (used for F 类规则)"
    )
    file_format: Optional[str] = Field(
        default=None, description="Image file format (jpg, png, webp...)"
    )
    caption: Optional[str] = Field(default=None, description="Caption or alt text")
    source: Optional[str] = Field(default=None, description="Credit/source line")
    photographer: Optional[str] = Field(default=None, description="Photographer name")
    license_expiry: Optional[str] = Field(
        default=None,
        description="ISO timestamp when media licence expires, used for F3 rules",
    )
    allow_png: bool = Field(
        default=False, description="Whether PNG usage is explicitly allowed"
    )
    allow_reason: Optional[str] = Field(
        default=None, description="Justification if PNG usage is allowed"
    )


class ArticleSection(BaseModel):
    """Logical sections extracted from article content."""

    kind: str = Field(description="Section type: introduction, body, conclusion, ...")
    content: str = Field(description="Plaintext or HTML fragment of the section")


class ArticlePayload(BaseModel):
    """Container describing an article passed into the proofreading pipeline."""

    article_id: Optional[int] = Field(default=None, description="Database id if any")
    title: str = Field(description="Article title")
    original_content: str = Field(description="Raw content as saved by the editor")
    html_content: Optional[str] = Field(
        default=None, description="Rendered HTML (if available)"
    )
    sections: List[ArticleSection] = Field(
        default_factory=list, description="Structured article sections"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for AI prompt context"
    )
    featured_image: Optional[ImageMetadata] = Field(
        default=None, description="Featured image metadata"
    )
    images: List[ImageMetadata] = Field(
        default_factory=list, description="Inline image metadata list"
    )
    keywords: List[str] = Field(
        default_factory=list, description="Keywords used for SEO context"
    )
    target_locale: str = Field(
        default="zh-TW", description="Locale variant controlling wording choices"
    )


class ProofreadingIssue(BaseModel):
    """Single rule violation returned by AI or deterministic engine."""

    rule_id: str = Field(description="Unique rule identifier, e.g. A1-001")
    category: str = Field(description="Top-level rule category (A-F)")
    subcategory: Optional[str] = Field(
        default=None, description="Secondary grouping (e.g. A1, B3, F2)"
    )
    message: str = Field(description="Human readable explanation of the issue")
    suggestion: Optional[str] = Field(
        default=None, description="Optional auto-fix suggestion"
    )
    severity: str = Field(
        description="Severity label (info, warning, error, critical)",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score in [0,1], from AI or script heuristics",
    )
    can_auto_fix: bool = Field(
        default=False, description="Whether the issue can be auto-fixed safely"
    )
    blocks_publish: bool = Field(
        default=False,
        description="If true, publishing must be blocked until resolved (F 类)",
    )
    source: RuleSource = Field(description="Origin of this issue (ai/script/merged)")
    attributed_by: Optional[str] = Field(
        default=None,
        description="AI model or rule engine id that produced the issue",
    )
    location: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional pointer to content location (paragraph index, offsets)",
    )
    evidence: Optional[str] = Field(
        default=None,
        description="Short excerpt or structured data to help reviewers verify",
    )


class ProofreadingStatistics(BaseModel):
    """Aggregated statistics for downstream analytics."""

    total_issues: int = Field(default=0)
    ai_issue_count: int = Field(default=0)
    script_issue_count: int = Field(default=0)
    blocking_issue_count: int = Field(default=0)
    categories: Dict[str, int] = Field(default_factory=dict)
    source_breakdown: Dict[str, int] = Field(default_factory=dict)


class ProcessingMetadata(BaseModel):
    """Metadata about AI + script processing execution."""

    ai_model: Optional[str] = Field(default=None)
    ai_latency_ms: Optional[int] = Field(default=None)
    prompt_tokens: Optional[int] = Field(default=None)
    completion_tokens: Optional[int] = Field(default=None)
    total_tokens: Optional[int] = Field(default=None)
    prompt_hash: Optional[str] = Field(
        default=None, description="Hash of prompt for regression tracking"
    )
    rule_manifest_version: Optional[str] = Field(
        default=None, description="Version fingerprint for deterministic rules"
    )
    script_engine_version: Optional[str] = Field(
        default=None, description="Semantic version for deterministic rule engine"
    )
    notes: Dict[str, Any] = Field(default_factory=dict)


class ProofreadingResult(BaseModel):
    """Unified payload combining AI output and deterministic checks."""

    article_id: Optional[int] = Field(default=None)
    issues: List[ProofreadingIssue] = Field(default_factory=list)
    suggested_content: Optional[str] = Field(
        default=None, description="AI generated suggested content revision"
    )
    seo_metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional SEO recommendations (if returned)"
    )
    ai_raw_response: Optional[Dict[str, Any]] = Field(
        default=None, description="Original parsed AI response for auditing"
    )
    statistics: ProofreadingStatistics = Field(
        default_factory=ProofreadingStatistics
    )
    processing_metadata: ProcessingMetadata = Field(
        default_factory=ProcessingMetadata
    )

    @property
    def blocking_issues(self) -> List[ProofreadingIssue]:
        """Return issues that block publishing."""
        return [issue for issue in self.issues if issue.blocks_publish]

