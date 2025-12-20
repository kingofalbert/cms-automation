"""Shared models for proofreading orchestration."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RuleSource(str, Enum):
    """Origin of a proofreading rule hit."""

    AI = "ai"
    SCRIPT = "script"
    MERGED = "merged"


class WarningLabel(str, Enum):
    """Warning labels for issues requiring manual verification.

    Used by G-class contextual validation rules to flag potential issues
    that need human review due to AI uncertainty or logical anomalies.
    """

    MANUAL_VERIFY = "manual_verify"  # 需手動驗證
    AI_HALLUCINATION = "ai_hallucination"  # 可能為AI幻覺
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"  # 地理邏輯異常
    SYMBOL_FORMAT = "symbol_format"  # 符號格式異常
    SENTENCE_INCOMPLETE = "sentence_incomplete"  # 語句不完整
    STRUCTURE_SUGGESTION = "structure_suggestion"  # 結構優化建議


class ImageMetadata(BaseModel):
    """Metadata for images referenced in an article."""

    id: str | None = Field(
        default=None, description="Unique identifier for the image (CMS/storage id)"
    )
    path: str | None = Field(
        default=None, description="Filesystem or object storage path"
    )
    url: str | None = Field(default=None, description="Remote URL if available")
    width: int | None = Field(
        default=None, description="Pixel width (used for F 类规则)"
    )
    height: int | None = Field(
        default=None, description="Pixel height (used for F 类规则)"
    )
    file_format: str | None = Field(
        default=None, description="Image file format (jpg, png, webp...)"
    )
    caption: str | None = Field(default=None, description="Caption or alt text")
    alt_text: str | None = Field(default=None, description="Alt text for accessibility (compatibility field)")
    source: str | None = Field(default=None, description="Credit/source line")
    photographer: str | None = Field(default=None, description="Photographer name")
    license_expiry: str | None = Field(
        default=None,
        description="ISO timestamp when media licence expires, used for F3 rules",
    )
    allow_png: bool = Field(
        default=False, description="Whether PNG usage is explicitly allowed"
    )
    allow_reason: str | None = Field(
        default=None, description="Justification if PNG usage is allowed"
    )


class ArticleSection(BaseModel):
    """Logical sections extracted from article content."""

    kind: str = Field(description="Section type: introduction, body, conclusion, ...")
    content: str = Field(description="Plaintext or HTML fragment of the section")


class ArticlePayload(BaseModel):
    """Container describing an article passed into the proofreading pipeline."""

    article_id: int | None = Field(default=None, description="Database id if any")
    title: str = Field(description="Article title")
    original_content: str = Field(description="Raw content as saved by the editor")
    html_content: str | None = Field(
        default=None, description="Rendered HTML (if available)"
    )
    sections: list[ArticleSection] = Field(
        default_factory=list, description="Structured article sections"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for AI prompt context"
    )
    featured_image: ImageMetadata | None = Field(
        default=None, description="Featured image metadata"
    )
    images: list[ImageMetadata] = Field(
        default_factory=list, description="Inline image metadata list"
    )
    keywords: list[str] = Field(
        default_factory=list, description="Keywords used for SEO context"
    )
    meta_description: str | None = Field(
        default=None, description="SEO meta description for deterministic rule checks"
    )
    seo_keywords: list[str] = Field(
        default_factory=list, description="SEO keywords for deterministic checks"
    )
    tags: list[str] = Field(
        default_factory=list, description="WordPress post tags"
    )
    categories: list[str] = Field(
        default_factory=list, description="WordPress post categories"
    )
    target_locale: str = Field(
        default="zh-TW", description="Locale variant controlling wording choices"
    )


class ProofreadingIssue(BaseModel):
    """Single rule violation returned by AI or deterministic engine."""

    rule_id: str = Field(description="Unique rule identifier, e.g. A1-001")
    category: str = Field(description="Top-level rule category (A-F)")
    subcategory: str | None = Field(
        default=None, description="Secondary grouping (e.g. A1, B3, F2)"
    )
    message: str = Field(description="Human readable explanation of the issue")
    original_text: str | None = Field(
        default=None, description="Original text snippet that has the issue"
    )
    suggestion: str | None = Field(
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
    attributed_by: str | None = Field(
        default=None,
        description="AI model or rule engine id that produced the issue",
    )
    location: dict[str, Any] | None = Field(
        default=None,
        description="Optional pointer to content location (paragraph index, offsets)",
    )
    evidence: str | None = Field(
        default=None,
        description="Short excerpt or structured data to help reviewers verify",
    )
    warning_label: str | None = Field(
        default=None,
        description="Warning label for manual verification (G-class rules): "
        "manual_verify, ai_hallucination, geographic_anomaly, symbol_format, "
        "sentence_incomplete, structure_suggestion",
    )


class ProofreadingStatistics(BaseModel):
    """Aggregated statistics for downstream analytics."""

    total_issues: int = Field(default=0)
    ai_issue_count: int = Field(default=0)
    script_issue_count: int = Field(default=0)
    blocking_issue_count: int = Field(default=0)
    categories: dict[str, int] = Field(default_factory=dict)
    source_breakdown: dict[str, int] = Field(default_factory=dict)


class ProcessingMetadata(BaseModel):
    """Metadata about AI + script processing execution."""

    ai_model: str | None = Field(default=None)
    ai_latency_ms: int | None = Field(default=None)
    prompt_tokens: int | None = Field(default=None)
    completion_tokens: int | None = Field(default=None)
    total_tokens: int | None = Field(default=None)
    prompt_hash: str | None = Field(
        default=None, description="Hash of prompt for regression tracking"
    )
    rule_manifest_version: str | None = Field(
        default=None, description="Version fingerprint for deterministic rules"
    )
    script_engine_version: str | None = Field(
        default=None, description="Semantic version for deterministic rule engine"
    )
    notes: dict[str, Any] = Field(default_factory=dict)


class ProofreadingResult(BaseModel):
    """Unified payload combining AI output and deterministic checks."""

    article_id: int | None = Field(default=None)
    issues: list[ProofreadingIssue] = Field(default_factory=list)
    suggested_content: str | None = Field(
        default=None, description="AI generated suggested content revision"
    )
    seo_metadata: dict[str, Any] | None = Field(
        default=None, description="Additional SEO recommendations (if returned)"
    )
    ai_raw_response: dict[str, Any] | None = Field(
        default=None, description="Original parsed AI response for auditing"
    )
    statistics: ProofreadingStatistics = Field(
        default_factory=ProofreadingStatistics
    )
    processing_metadata: ProcessingMetadata = Field(
        default_factory=ProcessingMetadata
    )

    @property
    def blocking_issues(self) -> list[ProofreadingIssue]:
        """Return issues that block publishing."""
        return [issue for issue in self.issues if issue.blocks_publish]

