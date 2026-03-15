"""FastAPI application entry point."""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from src.api.middleware.error_handler import ErrorHandlingMiddleware
from src.api.middleware.logging import LoggingMiddleware
from src.api.middleware.auth import AuthenticationMiddleware
from src.api.routes import register_routes
from src.config import get_settings, setup_logging
from src.config.database import get_db_config
from src.config.logging import get_logger

# Initialize logging
setup_logging()

_logger = get_logger(__name__)


async def _reap_stale_tasks(db_config) -> int:
    """Mark processing tasks older than 30 min as failed."""
    from sqlalchemy import and_, update

    from src.models.pipeline_task import PipelineTask

    cutoff = datetime.now(UTC) - timedelta(minutes=30)
    try:
        async with db_config.session() as session:
            result = await session.execute(
                update(PipelineTask)
                .where(and_(
                    PipelineTask.status == "processing",
                    PipelineTask.created_at < cutoff,
                ))
                .values(
                    status="failed",
                    error="Task timed out (stale reaper)",
                    completed_at=datetime.now(UTC),
                )
            )
            await session.commit()
            count = result.rowcount
            if count:
                _logger.info("stale_tasks_reaped", count=count)
            return count
    except Exception:
        _logger.warning("stale_task_reaper_failed", exc_info=True)
        return 0


async def _periodic_reaper(db_config) -> None:
    """Run stale task reaper every 10 minutes."""
    while True:
        await asyncio.sleep(600)
        await _reap_stale_tasks(db_config)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager.

    Handles startup and shutdown events.
    """
    from sqlalchemy import text

    # Startup
    settings = get_settings()
    app.state.settings = settings

    # Initialize database and pre-warm the connection pool.
    # Without this, the first /health check triggers engine creation +
    # DNS + TCP + TLS to Supabase, which takes 5-15s on Cloud Run cold
    # start and exceeds the 5s health check timeout.
    db_config = get_db_config()
    app.state.db_config = db_config

    try:
        async with db_config.session() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        # Non-fatal: pool will retry on first real request
        pass

    # Reap stale tasks at startup (clears stuck tasks from previous instances)
    await _reap_stale_tasks(db_config)

    # Start periodic reaper (every 10 minutes)
    reaper_task = asyncio.create_task(_periodic_reaper(db_config))

    yield

    # Shutdown
    reaper_task.cancel()
    try:
        await reaper_task
    except asyncio.CancelledError:
        pass
    await db_config.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    settings = get_settings()

    # Disable API docs in production
    is_production = settings.ENVIRONMENT == "production"
    app = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description="AI-powered CMS automation using Claude Computer Use API",
        lifespan=lifespan,
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    # Add compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Add custom middleware (order matters - last added is first executed)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(LoggingMiddleware)

    # Add authentication middleware
    # Set require_auth=False to disable auth (for testing/development)
    # In production, set SUPABASE_JWT_SECRET to enable auth
    require_auth = bool(settings.SUPABASE_JWT_SECRET)
    app.add_middleware(AuthenticationMiddleware, require_auth=require_auth)

    # Register API routes
    register_routes(app)

    return app


# Create application instance
app = create_app()


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint with database connectivity probe.

    Returns:
        dict: Health status including database connectivity
    """
    import asyncio

    from sqlalchemy import text

    db_config = get_db_config()
    db_status = "healthy"

    try:
        async with db_config.session() as session:
            await asyncio.wait_for(
                session.execute(text("SELECT 1")),
                timeout=5.0,
            )
    except Exception as exc:
        db_status = f"unhealthy: {type(exc).__name__}"

    overall = "healthy" if db_status == "healthy" else "degraded"
    return {"status": overall, "service": "cms-automation", "database": db_status}


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """Root endpoint redirect to docs."""
    return {
        "message": "CMS Automation API",
        "docs": "/docs",
        "health": "/health",
    }
