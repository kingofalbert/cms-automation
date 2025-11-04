"""Authentication middleware for FastAPI."""

from collections.abc import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.config.logging import get_logger

logger = get_logger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication integration.

    Note: This is a placeholder for CMS authentication integration.
    In production, this would integrate with the existing CMS authentication system.
    """

    # Paths that don't require authentication
    PUBLIC_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Verify authentication for protected routes.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            Response: HTTP response
        """
        # Skip authentication for public paths
        if request.url.path in self.PUBLIC_PATHS or request.url.path.startswith(
            "/docs"
        ):
            return await call_next(request)

        # Extract authorization header
        auth_header = request.headers.get("Authorization")

        # TODO: Integrate with CMS authentication system
        # For now, we'll use a simple token check
        if not auth_header:
            logger.warning(
                "missing_authentication",
                path=request.url.path,
                request_id=getattr(request.state, "request_id", "unknown"),
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Unauthorized",
                    "message": "Authentication required",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract token from header
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid authentication scheme")
        except ValueError:
            logger.warning(
                "invalid_auth_header",
                path=request.url.path,
                request_id=getattr(request.state, "request_id", "unknown"),
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Unauthorized",
                    "message": "Invalid authorization header format",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # TODO: Validate token with CMS authentication system
        # For development, we'll accept any token
        request.state.user_id = "dev_user"  # Placeholder

        return await call_next(request)
