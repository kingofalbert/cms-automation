"""Application settings model."""

from datetime import datetime

from sqlalchemy import JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base

try:  # Prefer JSONB when PostgreSQL dialect is available
    from sqlalchemy.dialects.postgresql import JSONB
except ImportError:  # pragma: no cover - fallback when dialect missing
    JSONB = None

JSONType = JSONB if JSONB is not None else JSON


class AppSettings(Base):
    """Singleton table storing application configuration."""

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=False, default=1
    )
    provider_config: Mapped[dict] = mapped_column(
        JSONType,
        nullable=False,
        default=dict,
        comment="Publishing provider configuration (playwright/computer_use/hybrid)",
    )
    cms_config: Mapped[dict] = mapped_column(
        JSONType,
        nullable=False,
        default=dict,
        comment="CMS connection details and preferences",
    )
    cost_limits: Mapped[dict] = mapped_column(
        JSONType,
        nullable=False,
        default=dict,
        comment="Cost thresholds and budgeting rules",
    )
    screenshot_retention: Mapped[dict] = mapped_column(
        JSONType,
        nullable=False,
        default=dict,
        comment="Screenshot retention policies (count, duration)",
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        comment="Last update timestamp",
    )

    def __repr__(self) -> str:
        return f"<AppSettings(id={self.id}, updated_at={self.updated_at.isoformat()})>"
