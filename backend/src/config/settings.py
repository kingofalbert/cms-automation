"""Application configuration management using Pydantic settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get project root (parent of backend directory)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application Configuration
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment",
    )
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    SECRET_KEY: str = Field(
        ...,
        description="Secret key for session management and JWT signing",
        min_length=32,
    )
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS allowed origins",
    )

    # API Configuration
    API_PORT: int = Field(default=8000, ge=1000, le=65535)
    API_HOST: str = Field(default="0.0.0.0")
    API_TITLE: str = Field(default="CMS Automation API")
    API_VERSION: str = Field(default="1.0.0")

    # Database Configuration
    DATABASE_URL: PostgresDsn = Field(
        ...,
        description="PostgreSQL connection string",
    )
    DATABASE_POOL_SIZE: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Database connection pool size",
    )
    DATABASE_MAX_OVERFLOW: int = Field(
        default=10,
        ge=0,
        le=50,
        description="Maximum overflow connections",
    )
    DATABASE_POOL_TIMEOUT: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Pool timeout in seconds",
    )
    DATABASE_POOL_RECYCLE: int = Field(
        default=3600,
        ge=60,
        description="Connection recycle time in seconds",
    )

    # Redis Configuration
    REDIS_URL: RedisDsn = Field(
        ...,
        description="Redis connection string",
    )
    REDIS_MAX_CONNECTIONS: int = Field(default=50, ge=1)

    # Anthropic API Configuration
    ANTHROPIC_API_KEY: str = Field(
        ...,
        description="Anthropic Claude API key",
        min_length=10,
    )
    ANTHROPIC_MODEL: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Claude model to use for generation",
    )
    ANTHROPIC_MAX_TOKENS: int = Field(
        default=4096,
        ge=1,
        le=8192,
        description="Maximum tokens for Claude responses",
    )

    # CMS Integration
    CMS_TYPE: Literal["wordpress", "strapi", "contentful", "ghost"] = Field(
        default="wordpress",
        description="CMS platform type",
    )
    CMS_BASE_URL: str = Field(
        ...,
        description="CMS base URL",
    )
    CMS_USERNAME: str = Field(
        default="",
        description="CMS username (for WordPress application password auth)",
    )
    CMS_APPLICATION_PASSWORD: str = Field(
        default="",
        description="CMS application password",
    )
    CMS_API_TOKEN: str = Field(
        default="",
        description="CMS API token (for token-based auth)",
    )

    # Article Generation Settings
    MAX_ARTICLE_WORD_COUNT: int = Field(default=10000, ge=100, le=50000)
    MIN_ARTICLE_WORD_COUNT: int = Field(default=100, ge=50, le=1000)
    DEFAULT_ARTICLE_WORD_COUNT: int = Field(default=1000, ge=100)
    MAX_ARTICLE_GENERATION_TIME: int = Field(
        default=300,
        ge=30,
        le=600,
        description="Maximum time for article generation in seconds",
    )
    MAX_ARTICLE_COST: float = Field(
        default=0.50,
        ge=0.01,
        le=10.0,
        description="Maximum cost per article in USD",
    )

    # Feature Flags
    ENABLE_SEMANTIC_SIMILARITY: bool = Field(
        default=True,
        description="Enable duplicate detection via semantic similarity",
    )
    SIMILARITY_THRESHOLD: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Cosine similarity threshold for duplicate detection",
    )
    MAX_CONCURRENT_GENERATIONS: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum concurrent article generation tasks",
    )

    # Retry Configuration
    MAX_RETRIES: int = Field(default=3, ge=0, le=10)
    RETRY_DELAY: int = Field(
        default=300,
        ge=1,
        description="Retry delay in seconds",
    )

    # Monitoring
    ENABLE_METRICS: bool = Field(default=True)
    METRICS_PORT: int = Field(default=9090, ge=1000, le=65535)

    # Celery Configuration
    CELERY_BROKER_URL: str | None = Field(default=None)
    CELERY_RESULT_BACKEND: str | None = Field(default=None)
    CELERY_TASK_SERIALIZER: str = Field(default="json")
    CELERY_RESULT_SERIALIZER: str = Field(default="json")
    CELERY_ACCEPT_CONTENT: list[str] = Field(default=["json"])
    CELERY_TIMEZONE: str = Field(default="UTC")
    CELERY_ENABLE_UTC: bool = Field(default=True)
    CELERY_TASK_TRACK_STARTED: bool = Field(default=True)
    CELERY_TASK_TIME_LIMIT: int = Field(default=600, ge=60)
    CELERY_TASK_SOFT_TIME_LIMIT: int = Field(default=540, ge=30)
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = Field(default=4, ge=1)
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = Field(default=1000, ge=1)

    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def set_celery_broker_url(cls, v: str | None, info) -> str:
        """Set Celery broker URL from REDIS_URL if not provided."""
        if v is not None:
            return v
        redis_url = info.data.get("REDIS_URL")
        if redis_url:
            return str(redis_url)
        raise ValueError("Either CELERY_BROKER_URL or REDIS_URL must be set")

    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def set_celery_result_backend(cls, v: str | None, info) -> str:
        """Set Celery result backend from REDIS_URL if not provided."""
        if v is not None:
            return v
        redis_url = info.data.get("REDIS_URL")
        if redis_url:
            return str(redis_url)
        raise ValueError("Either CELERY_RESULT_BACKEND or REDIS_URL must be set")

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: str | list[str]) -> list[str]:
        """Parse ALLOWED_ORIGINS from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("CELERY_ACCEPT_CONTENT", mode="before")
    @classmethod
    def parse_celery_accept_content(cls, v: str | list[str]) -> list[str]:
        """Parse CELERY_ACCEPT_CONTENT from comma-separated string."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",")]
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    This function uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()
