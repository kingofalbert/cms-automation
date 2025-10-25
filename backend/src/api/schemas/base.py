"""Base Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        str_strip_whitespace=True,
    )


class TimestampSchema(BaseSchema):
    """Schema mixin for created_at and updated_at timestamps."""

    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record last update timestamp")


class PaginationParams(BaseSchema):
    """Query parameters for pagination."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Number of items per page"
    )

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for database query."""
        return self.page_size


class PaginatedResponse(BaseSchema, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T] = Field(..., description="List of items for current page")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Number of items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

    @classmethod
    def create(
        cls, items: list[T], total: int, page: int, page_size: int
    ) -> "PaginatedResponse[T]":
        """Create paginated response from query results.

        Args:
            items: List of items for current page
            total: Total number of items
            page: Current page number
            page_size: Number of items per page

        Returns:
            PaginatedResponse: Paginated response object
        """
        total_pages = (total + page_size - 1) // page_size  # Ceiling division
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class ErrorResponse(BaseSchema):
    """Standard error response format."""

    error: str = Field(..., description="Error type or category")
    message: str = Field(..., description="Human-readable error message")
    request_id: str | None = Field(None, description="Request ID for debugging")
    details: dict[str, str] | None = Field(
        None, description="Additional error details"
    )


class SuccessResponse(BaseSchema):
    """Standard success response format."""

    success: bool = Field(default=True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: dict | None = Field(None, description="Additional response data")
