"""API route registration."""

from fastapi import FastAPI

from src.api.routes import articles, topics
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

    logger.info("api_routes_registered", route_count=2)
