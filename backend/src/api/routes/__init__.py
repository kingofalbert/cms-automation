"""API route registration."""

from fastapi import FastAPI

from src.api.routes import (
    analytics_routes,
    articles,
    computer_use,
    debug_routes,
    files_routes,
    image_alt_routes,
    import_routes,
    monitoring_routes,
    # optimization_monitoring_routes,  # Temporarily disabled - service not available
    optimization_routes,
    parsing_routes,
    proofreading_decisions,
    proofreading_routes,  # Independent proofreading service (body text only)
    publish_routes,
    seo_routes,
    settings_routes,
    title_generation_routes,
    topics,
    worklist_routes,
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
    app.include_router(parsing_routes.router, prefix="/v1", tags=["Article Parsing"])
    app.include_router(optimization_routes.router, prefix="/v1", tags=["AI Optimization"])
    app.include_router(import_routes.router, prefix="/v1", tags=["Import"])
    app.include_router(seo_routes.router, prefix="/v1", tags=["SEO Analysis"])
    app.include_router(files_routes.router, tags=["Files"])  # Already has /v1/files prefix
    app.include_router(computer_use.router, prefix="/v1", tags=["Computer Use"])
    app.include_router(publish_routes.router, prefix="/v1", tags=["Publishing"])
    app.include_router(monitoring_routes.router, prefix="/v1", tags=["Monitoring"])
    # app.include_router(optimization_monitoring_routes.router, prefix="/v1", tags=["Optimization Monitoring"])  # Temporarily disabled
    app.include_router(analytics_routes.router, prefix="/v1", tags=["Analytics"])
    app.include_router(settings_routes.router, prefix="/v1", tags=["Settings"])
    app.include_router(title_generation_routes.router, tags=["Title Generation"])  # Already has /v1 prefix
    app.include_router(proofreading_routes.router, tags=["Proofreading"])  # Independent proofreading service (body text only) - Already has /v1 prefix
    app.include_router(worklist_routes.router, prefix="/v1", tags=["Worklist"])
    app.include_router(image_alt_routes.router, tags=["Image Alt Generation"])  # Already has /v1/images prefix
    app.include_router(debug_routes.router, tags=["Debug"])  # Debug endpoints

    # Note: proofreading_decisions router already has its own prefix
    app.include_router(proofreading_decisions.router)

    # Include enhanced proofreading routes
    from src.api.routes.proofreading_decisions_enhanced import router as enhanced_router
    app.include_router(enhanced_router)

    # Include Claude-powered proofreading routes
    from src.api.routes.proofreading_decisions_claude import router as claude_router
    app.include_router(claude_router)

    logger.info("api_routes_registered", route_count=15)  # Added Optimization Monitoring routes
