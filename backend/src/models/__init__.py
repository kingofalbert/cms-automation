"""SQLAlchemy data models for CMS automation."""

from src.models.analytics import ProviderMetrics
from src.models.article import Article, ArticleStatus
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
from src.models.settings import AppSettings
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
    # Topic Request
    "TopicRequest",
    "TopicRequestStatus",
    "TopicRequestPriority",
    "TopicEmbedding",
    # SEO
    "SEOMetadata",
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
