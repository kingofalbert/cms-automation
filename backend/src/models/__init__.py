"""SQLAlchemy data models for CMS automation."""

from src.models.analytics import ProviderMetrics
from src.models.article import Article, ArticleStatus, ArticleStatusHistory
from src.models.article_faq import ArticleFAQ, FAQQuestionType, FAQSearchIntent, FAQStatus
from src.models.article_image import ArticleImage, ArticleImageReview, ImageReviewAction
from src.models.base import Base, SoftDeleteMixin, TimestampMixin
from src.models.proofreading import (
    DecisionType,
    FeedbackStatus,
    FeedbackTuningJob,
    ProofreadingDecision,
    ProofreadingHistory,
    TuningJobStatus,
    TuningJobType,
)
from src.models.publish import (
    ExecutionLog,
    LogLevel,
    Provider,
    PublishTask,
    TaskStatus,
)
from src.models.seo import SEOMetadata
from src.models.seo_suggestions import SEOSuggestion
from src.models.settings import AppSettings
from src.models.title_suggestions import TitleSuggestion
from src.models.topic_embedding import TopicEmbedding
from src.models.topic_request import (
    TopicRequest,
    TopicRequestPriority,
    TopicRequestStatus,
)
from src.models.uploaded_file import UploadedFile
from src.models.worklist import WorklistItem, WorklistStatus

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",
    # Article
    "Article",
    "ArticleStatus",
    "ArticleStatusHistory",
    # Article Images (Phase 7)
    "ArticleImage",
    "ArticleImageReview",
    "ImageReviewAction",
    # Article FAQs (Phase 7 - Unified Optimization)
    "ArticleFAQ",
    "FAQQuestionType",
    "FAQSearchIntent",
    "FAQStatus",
    # Topic Request
    "TopicRequest",
    "TopicRequestStatus",
    "TopicRequestPriority",
    "TopicEmbedding",
    # SEO
    "SEOMetadata",
    # SEO Suggestions (Phase 7 - Unified Optimization)
    "SEOSuggestion",
    # Title Suggestions (Phase 7 - Unified Optimization)
    "TitleSuggestion",
    # Publishing
    "PublishTask",
    "Provider",
    "TaskStatus",
    "ExecutionLog",
    "LogLevel",
    # Analytics
    "ProviderMetrics",
    # Settings
    "AppSettings",
    # Worklist
    "WorklistItem",
    "WorklistStatus",
    # Storage
    "UploadedFile",
    # Proofreading
    "DecisionType",
    "FeedbackStatus",
    "TuningJobType",
    "TuningJobStatus",
    "ProofreadingHistory",
    "ProofreadingDecision",
    "FeedbackTuningJob",
]
