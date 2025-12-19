"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from src.api.middleware.error_handler import ErrorHandlingMiddleware
from src.api.middleware.logging import LoggingMiddleware
from src.api.middleware.auth import AuthenticationMiddleware
from src.api.routes import register_routes
from src.config import get_settings, setup_logging
from src.config.database import get_db_config

# Initialize logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    settings = get_settings()
    app.state.settings = settings

    # Initialize database
    db_config = get_db_config()
    app.state.db_config = db_config

    yield

    # Shutdown
    await db_config.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description="AI-powered CMS automation using Claude Computer Use API",
        lifespan=lifespan,
        docs_url="/docs",  # Always enable docs
        redoc_url="/redoc",  # Always enable ReDoc
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        dict: Health status
    """
    return {"status": "healthy", "service": "cms-automation"}


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """Root endpoint redirect to docs."""
    return {
        "message": "CMS Automation API",
        "docs": "/docs",
        "health": "/health",
    }
