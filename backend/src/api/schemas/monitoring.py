"""Schemas for task monitoring endpoints."""

from datetime import datetime

from pydantic import Field

from src.api.schemas.base import BaseSchema


class TaskFilters(BaseSchema):
    """Query filters for monitoring task list."""

    status: str | None = Field(
        default=None,
        description="Optional status filter (completed, failed, in_progress, etc.)",
    )
    provider: str | None = Field(
        default=None,
        description="Optional provider filter (playwright, computer_use, hybrid)",
    )
    limit: int = Field(default=50, ge=1, le=200, description="Maximum records to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


class TaskStatistics(BaseSchema):
    """Aggregate publishing task statistics."""

    total: int = Field(..., ge=0, description="Total number of tasks")
    completed: int = Field(..., ge=0, description="Completed tasks count")
    failed: int = Field(..., ge=0, description="Failed tasks count")
    in_progress: int = Field(..., ge=0, description="In-progress tasks count")


class ExecutionLogEntry(BaseSchema):
    """Execution log entry payload."""

    id: int = Field(..., description="Unique log identifier")
    task_id: int = Field(..., description="Associated publishing task ID")
    created_at: datetime = Field(..., description="Log creation timestamp")
    log_level: str | None = Field(
        default=None, description="Log level (INFO, WARNING, ERROR, etc.)"
    )
    step_name: str | None = Field(
        default=None, description="Workflow step associated with the log entry"
    )
    message: str | None = Field(
        default=None, description="Human-readable log message"
    )
    action_type: str | None = Field(
        default=None, description="Action type performed during the step"
    )
    action_target: str | None = Field(
        default=None, description="Target selector or URL of the action"
    )
    action_result: str | None = Field(
        default=None, description="Outcome of the action (success, failure, etc.)"
    )
    screenshot_url: str | None = Field(
        default=None, description="Optional screenshot associated with the log"
    )
    details: dict | None = Field(
        default=None, description="Structured diagnostic data for the log entry"
    )
