"""Article model for generated content."""

from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.article_faq import ArticleFAQ
    from src.models.article_image import ArticleImage, ArticleImageReview
    from src.models.proofreading import ProofreadingDecision, ProofreadingHistory
    from src.models.publish import PublishTask
    from src.models.seo import SEOMetadata
    from src.models.seo_suggestions import SEOSuggestion
    from src.models.title_suggestions import TitleSuggestion
    from src.models.topic_request import TopicRequest
    from src.models.uploaded_file import UploadedFile


class ArticleStatus(str, PyEnum):
    """Article workflow status."""

    IMPORTED = "imported"
    DRAFT = "draft"
    IN_REVIEW = "in-review"
    SEO_OPTIMIZED = "seo_optimized"
    READY_TO_PUBLISH = "ready_to_publish"
    PUBLISHING = "publishing"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class Article(Base, TimestampMixin):
    """Generated article content."""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Content
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Article headline",
    )
    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full article content (Markdown or HTML)",
    )
    raw_html: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Original HTML from Google Docs export (for parser with images)",
    )

    # Status and workflow
    status: Mapped[ArticleStatus] = mapped_column(
        Enum(ArticleStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ArticleStatus.DRAFT,
        index=True,
        comment="Workflow status",
    )

    # Authorship
    author_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="User who initiated generation",
    )

    # Article source tracking
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual",
        index=True,
        comment="Article import source (csv_import, json_import, manual, wordpress_export)",
    )

    # Image management
    featured_image_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Path to featured image in storage",
    )

    additional_images: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Array of additional image paths",
    )

    # WordPress taxonomy
    tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(100)),
        nullable=True,
        default=list,
        comment="WordPress post tags (3-6 natural categories for internal navigation)",
    )

    categories: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(100)),
        nullable=True,
        default=list,
        comment="WordPress post categories (hierarchical taxonomy)",
    )

    # Phase 10: WordPress primary category (single selection from candidate list)
    primary_category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="WordPress primary category (主分類，從候選列表匹配)",
    )

    # Phase 11: WordPress secondary categories (multiple selection for cross-listing)
    secondary_categories: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(100)),
        nullable=True,
        default=list,
        comment="WordPress secondary categories (副分類，可多選，用於交叉列表)",
    )

    proofreading_issues: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="Combined AI/script proofreading issues",
    )
    critical_issues_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Count of blocking (F-class) issues",
    )

    # AI优化建议字段 (Proofreading Review Workflow)
    # Content optimization
    suggested_content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="AI-optimized article content",
    )
    suggested_content_changes: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Diff data structure for content changes",
    )

    # Meta description suggestions
    suggested_meta_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="AI-suggested meta description",
    )
    suggested_meta_reasoning: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="AI reasoning for meta description suggestion",
    )
    suggested_meta_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Meta description quality score (0-1)",
    )

    # Title suggestions (Phase 7.5: Unified parsing)
    suggested_titles: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="AI-suggested title variations (2-3 options with scores)",
    )

    # SEO keywords suggestions
    suggested_seo_keywords: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
        comment="AI-suggested SEO keywords array",
    )
    suggested_keywords_reasoning: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="AI reasoning for SEO keywords",
    )
    suggested_keywords_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="SEO keywords quality score (0-1)",
    )

    # Paragraph and structure suggestions
    paragraph_suggestions: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Paragraph optimization suggestions",
    )
    paragraph_split_suggestions: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Paragraph splitting recommendations",
    )

    # FAQ schema proposals
    faq_schema_proposals: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Multiple FAQ schema variants for review",
    )

    # AI generation metadata
    suggested_generated_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        comment="Timestamp when AI suggestions were generated",
    )
    ai_model_used: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="AI model identifier used for suggestions",
    )
    generation_cost: Mapped[float | None] = mapped_column(
        Numeric(10, 4),
        nullable=True,
        comment="API cost for generating suggestions (USD)",
    )

    # Phase 7: Article Structured Parsing Fields
    # Title decomposition
    title_prefix: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment='First part of title (optional), e.g., "【專題報導】"',
    )

    title_main: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment='Main title (required for new articles), e.g., "2024年醫療保健創新趨勢"',
    )

    title_suffix: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment='Subtitle/suffix (optional), e.g., "從AI診斷到遠距醫療"',
    )

    # Author information
    author_line: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
        comment='Raw author line from document, e.g., "文／張三｜編輯／李四"',
    )

    author_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment='Cleaned author name extracted from author_line, e.g., "張三"',
    )

    # Cleaned body content
    body_html: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Sanitized body HTML with headers/images/meta removed, ready for publishing",
    )

    # SEO and metadata
    meta_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Extracted meta description for SEO (150-160 chars recommended)",
    )

    seo_keywords: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
        comment="Array of SEO keywords extracted from content",
    )

    # Phase 10: Yoast SEO focus keyword
    focus_keyword: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Yoast SEO focus keyword (從 seo_keywords 中選取或 AI 推薦)",
    )

    # Phase 12: Related articles for internal linking
    related_articles: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="AI-recommended related articles for internal linking (from Supabase health_articles)",
    )

    # Phase 9: SEO Title (separate from H1 title)
    seo_title: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment='SEO Title Tag (30字左右，用於<title>標籤和搜尋結果顯示)',
    )

    seo_title_extracted: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        server_default="false",
        comment='是否從原文中提取了標記的 SEO Title',
    )

    seo_title_source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment='SEO Title 來源：extracted/ai_generated/user_input/migrated',
    )

    # Parsing workflow
    parsing_method: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Parsing method used: 'ai' or 'heuristic'",
    )

    parsing_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Confidence score of parsing (0.0-1.0)",
    )

    parsing_confirmed: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        server_default="false",
        comment="Whether parsing has been reviewed and confirmed by user (Step 1)",
    )

    parsing_confirmed_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        comment="Timestamp when parsing was confirmed",
    )

    parsing_confirmed_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="User ID or identifier who confirmed the parsing",
    )

    parsing_feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="User feedback on parsing quality during confirmation",
    )

    # CMS integration
    cms_article_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        comment="CMS platform's article ID",
    )

    published_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        index=True,
        comment="Public URL after publishing to CMS",
    )

    # Publishing
    published_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        index=True,
        comment="Actual publication timestamp",
    )

    # Phase 7: Unified AI Optimization metadata
    unified_optimization_generated: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        index=True,
        comment="Whether unified AI optimizations have been generated",
    )
    unified_optimization_generated_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        comment="When unified AI optimizations were generated",
    )
    unified_optimization_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 6),
        nullable=True,
        comment="Cost in USD for generating all optimizations",
    )

    # FAQ Assessment (v2.2)
    faq_applicable: Mapped[bool | None] = mapped_column(
        nullable=True,
        comment="Whether FAQ is applicable for this article (null=not assessed)",
    )
    faq_assessment: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="FAQ applicability assessment details (reason, pain_points)",
    )
    faq_editorial_notes: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="FAQ editorial notes (longtail keywords, multimedia suggestions)",
    )
    faq_html: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Generated FAQ HTML section for article body",
    )

    # Extracted FAQs from original article (Phase 14: FAQ Comparison)
    extracted_faqs: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="FAQs extracted from existing article HTML (e.g., marked with 【FAQ開始】)",
    )
    extracted_faqs_detection_method: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="How extracted FAQs were detected: text_markers, html_comment, css_class, etc.",
    )

    # Phase 15: AEO (Answer Engine Optimization) fields
    aeo_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="AEO type from document (e.g., 定義解說型, 步驟操作型, 列表型)",
    )
    aeo_paragraph: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="AEO first paragraph optimized for search engine answer boxes",
    )

    # Phase 15: SEO title variants from document
    seo_title_variants: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="SEO title variants from doc [{type: '資訊型', title: '...'}, {type: '懸念型', title: '...'}]",
    )

    # Phase 15: Document proofreading suggestions (from 校對結果 section)
    doc_proofreading_suggestions: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Proofreading suggestions from document's 校對結果 section",
    )

    # Phase 15: Document image alt texts (from 圖片 Alt Text section)
    doc_image_alt_texts: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Image alt texts from document's 圖片 Alt Text section with Drive links",
    )

    # Metadata
    article_metadata: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="CMS-specific metadata (featured image, excerpt, etc.)",
    )
    formatting: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Formatting preferences (headings, lists, code blocks)",
    )

    # Relationships
    topic_request: Mapped["TopicRequest"] = relationship(
        "TopicRequest",
        back_populates="article",
        foreign_keys="TopicRequest.article_id",
    )

    # SEO metadata (1:1 relationship)
    seo_metadata: Mapped[Optional["SEOMetadata"]] = relationship(
        "SEOMetadata",
        back_populates="article",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Publishing tasks (1:N relationship)
    publish_tasks: Mapped[list["PublishTask"]] = relationship(
        "PublishTask",
        back_populates="article",
        cascade="all, delete-orphan",
    )

    # Uploaded files (1:N relationship)
    uploaded_files: Mapped[list["UploadedFile"]] = relationship(
        "UploadedFile",
        back_populates="article",
        cascade="all, delete-orphan",
        foreign_keys="UploadedFile.article_id",
    )

    # Proofreading relationships (1:N)
    proofreading_histories: Mapped[list["ProofreadingHistory"]] = relationship(
        "ProofreadingHistory",
        back_populates="article",
        cascade="all, delete-orphan",
    )

    proofreading_decisions: Mapped[list["ProofreadingDecision"]] = relationship(
        "ProofreadingDecision",
        back_populates="article",
        cascade="all, delete-orphan",
    )

    status_history: Mapped[list["ArticleStatusHistory"]] = relationship(
        "ArticleStatusHistory",
        back_populates="article",
        cascade="all, delete-orphan",
        order_by="ArticleStatusHistory.created_at",
    )

    # Phase 7: Article Images relationships (1:N)
    article_images: Mapped[list["ArticleImage"]] = relationship(
        "ArticleImage",
        back_populates="article",
        cascade="all, delete-orphan",
        order_by="ArticleImage.position",
    )

    # Phase 7: Unified AI Optimization relationships
    # Title suggestions (1:1 relationship)
    title_suggestion: Mapped[Optional["TitleSuggestion"]] = relationship(
        "TitleSuggestion",
        back_populates="article",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # SEO suggestions (1:1 relationship)
    seo_suggestion: Mapped[Optional["SEOSuggestion"]] = relationship(
        "SEOSuggestion",
        back_populates="article",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Article FAQs (1:N relationship)
    faqs: Mapped[list["ArticleFAQ"]] = relationship(
        "ArticleFAQ",
        back_populates="article",
        cascade="all, delete-orphan",
        order_by="ArticleFAQ.position",
    )

    def __repr__(self) -> str:
        """String representation.

        Handles DetachedInstanceError gracefully when session is closed.
        """
        try:
            title_preview = self.title[:50] if self.title else "N/A"
            return f"<Article(id={self.id}, status={self.status}, title='{title_preview}...')>"
        except Exception:
            # Handle detached instance or other errors gracefully
            return f"<Article(id={self.id})>"

    @property
    def word_count(self) -> int:
        """Calculate approximate word count of article body."""
        return len(self.body.split())

    @property
    def is_published(self) -> bool:
        """Check if article is published."""
        return self.status == ArticleStatus.PUBLISHED and self.published_at is not None

    @property
    def has_seo(self) -> bool:
        """Check if article has SEO metadata."""
        return self.seo_metadata is not None

    @property
    def has_featured_image(self) -> bool:
        """Check if article has a featured image."""
        return self.featured_image_path is not None

    @property
    def image_count(self) -> int:
        """Count total images (featured + additional)."""
        count = 1 if self.featured_image_path else 0
        if self.additional_images:
            count += len(self.additional_images)
        return count

    @property
    def latest_publish_task(self) -> Optional["PublishTask"]:
        """Get the most recent publishing task."""
        if not self.publish_tasks:
            return None
        return max(self.publish_tasks, key=lambda t: t.created_at)

    @property
    def successful_publishes(self) -> int:
        """Count number of successful publishing tasks."""
        if not self.publish_tasks:
            return 0
        return sum(1 for task in self.publish_tasks if task.status == "completed")


class ArticleStatusHistory(Base):
    """Audit log capturing every article status transition."""

    __tablename__ = "article_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    old_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Previous article status value",
    )
    new_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="New article status value",
    )
    changed_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="User id or 'system' for automated transitions",
    )
    change_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Optional description of why the transition occurred",
    )
    change_metadata: Mapped[dict] = mapped_column(
        "metadata",  # Map to database column 'metadata'
        JSONB,
        nullable=False,
        default=dict,
        comment="Structured metadata describing the transition context",
    )
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        index=True,
        comment="Timestamp when the status change occurred",
    )

    article: Mapped["Article"] = relationship(
        "Article",
        back_populates="status_history",
    )
