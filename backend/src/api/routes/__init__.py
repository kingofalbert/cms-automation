"""API route registration."""

from fastapi import FastAPI

from src.api.routes import (
    articles,
    computer_use,
    files_routes,
    import_routes,
    seo_routes,
    topics,
)
from src.config.logging import get_logger

logger = get_logger(__name__)


def register_routes(app: FastAPI) -> None:
    """Register all API routes with the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Register route modules
    app.include_router(topics.router, prefix="/v1/topics", tags=["Topics"])
    app.include_router(articles.router, prefix="/v1/articles", tags=["Articles"])
    app.include_router(import_routes.router, prefix="/v1", tags=["Import"])
    app.include_router(seo_routes.router, prefix="/v1", tags=["SEO Analysis"])
    app.include_router(files_routes.router, tags=["Files"])  # Already has /v1/files prefix
    app.include_router(computer_use.router, prefix="/v1", tags=["Computer Use"])

    logger.info("api_routes_registered", route_count=6)
