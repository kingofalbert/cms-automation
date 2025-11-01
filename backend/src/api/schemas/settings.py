"""Settings management schemas."""

from datetime import datetime
from typing import Any, Dict

from pydantic import Field

from src.api.schemas.base import BaseSchema


class SettingsResponse(BaseSchema):
    """Application settings payload."""

    provider_config: Dict[str, Any] = Field(
        default_factory=dict, description="Publishing provider configuration"
    )
    cms_config: Dict[str, Any] = Field(
        default_factory=dict, description="CMS integration configuration"
    )
    cost_limits: Dict[str, Any] = Field(
        default_factory=dict, description="Cost control limits and alerts"
    )
    screenshot_retention: Dict[str, Any] = Field(
        default_factory=dict, description="Screenshot retention policy"
    )
    updated_at: datetime = Field(..., description="Last updated timestamp")


class SettingsUpdateRequest(BaseSchema):
    """Payload for updating application settings."""

    provider_config: Dict[str, Any] | None = Field(
        default=None, description="Updated provider configuration"
    )
    cms_config: Dict[str, Any] | None = Field(
        default=None, description="Updated CMS configuration"
    )
    cost_limits: Dict[str, Any] | None = Field(
        default=None, description="Updated cost limits"
    )
    screenshot_retention: Dict[str, Any] | None = Field(
        default=None, description="Updated screenshot retention policy"
    )


class ConnectionTestRequest(BaseSchema):
    """Request payload to test CMS connection."""

    cms_type: str | None = Field(
        default=None,
        description="CMS type to test (default: value from stored settings)",
    )
    base_url: str | None = Field(
        default=None,
        description="CMS base URL override",
    )
    username: str | None = Field(
        default=None, description="CMS username (WordPress application user)"
    )
    application_password: str | None = Field(
        default=None, description="CMS application password"
    )
    api_token: str | None = Field(
        default=None,
        description="CMS API token for token-based authentication",
    )


class ConnectionTestResponse(BaseSchema):
    """Response payload for CMS connection test."""

    success: bool = Field(..., description="Indicates if connection test succeeded")
    message: str = Field(..., description="Human readable summary")
    details: Dict[str, Any] | None = Field(
        default=None, description="Additional diagnostic information"
    )
