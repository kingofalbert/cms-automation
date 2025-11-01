"""API route registration."""

from fastapi import FastAPI

from src.api.routes import (
    analytics_routes,
    articles,
    computer_use,
    files_routes,
    import_routes,
    monitoring_routes,
    publish_routes,
    seo_routes,
    settings_routes,
    worklist_routes,
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
    app.include_router(publish_routes.router, prefix="/v1", tags=["Publishing"])
    app.include_router(monitoring_routes.router, prefix="/v1", tags=["Monitoring"])
    app.include_router(analytics_routes.router, prefix="/v1", tags=["Analytics"])
    app.include_router(settings_routes.router, prefix="/v1", tags=["Settings"])
    app.include_router(worklist_routes.router, prefix="/v1", tags=["Worklist"])

    logger.info("api_routes_registered", route_count=11)
