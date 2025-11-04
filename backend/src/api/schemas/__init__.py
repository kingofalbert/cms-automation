"""API schemas for request/response validation."""

from src.api.schemas.analytics import (
    CostUsageEntry,
    ProviderMetric,
    RecommendationsResponse,
    StorageUsageEntry,
)
from src.api.schemas.base import (
    BaseSchema,
    ErrorResponse,
    PaginatedResponse,
    PaginationParams,
    SuccessResponse,
    TimestampSchema,
)
from src.api.schemas.monitoring import ExecutionLogEntry, TaskFilters, TaskStatistics
from src.api.schemas.proofreading import (
    ProcessingMetadataSchema,
    ProofreadingIssueSchema,
    ProofreadingResponse,
    ProofreadingStatisticsSchema,
)
from src.api.schemas.publishing import (
    PublishOptions,
    PublishRequest,
    PublishResult,
    PublishTaskResponse,
    Screenshot,
)
from src.api.schemas.settings import (
    ConnectionTestRequest,
    ConnectionTestResponse,
    SettingsResponse,
    SettingsUpdateRequest,
)
from src.api.schemas.worklist import (
    WorklistItemResponse,
    WorklistStatisticsResponse,
    WorklistStatusUpdateRequest,
    WorklistSyncStatusResponse,
    WorklistSyncTriggerResponse,
)

__all__ = [
    "BaseSchema",
    "TimestampSchema",
    "PaginationParams",
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
    "ProofreadingIssueSchema",
    "ProofreadingStatisticsSchema",
    "ProcessingMetadataSchema",
    "ProofreadingResponse",
    "PublishOptions",
    "PublishRequest",
    "PublishResult",
    "PublishTaskResponse",
    "Screenshot",
    "TaskFilters",
    "TaskStatistics",
    "ExecutionLogEntry",
    "ProviderMetric",
    "CostUsageEntry",
    "StorageUsageEntry",
    "RecommendationsResponse",
    "SettingsResponse",
    "SettingsUpdateRequest",
    "ConnectionTestRequest",
    "ConnectionTestResponse",
    "WorklistItemResponse",
    "WorklistStatisticsResponse",
    "WorklistSyncStatusResponse",
    "WorklistStatusUpdateRequest",
    "WorklistSyncTriggerResponse",
]
