"""Authentication middleware for FastAPI with Supabase JWT verification."""

import hmac
from collections.abc import Callable
from typing import Optional

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.config.logging import get_logger
from src.config.settings import get_settings
from src.services.auth.jwt import get_jwt_verifier

logger = get_logger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for Supabase JWT authentication.

    Verifies JWT tokens issued by Supabase Auth and extracts user information.
    """

    # Paths that don't require authentication
    PUBLIC_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    # Path prefixes that don't require authentication
    PUBLIC_PREFIXES = (
        "/docs",
        "/redoc",
    )

    def __init__(self, app, require_auth: bool = True):
        """Initialize the middleware.

        Args:
            app: FastAPI application
            require_auth: Whether to require authentication (can be disabled for testing)
        """
        super().__init__(app)
        self.require_auth = require_auth
        self._jwt_verifier = None

    @property
    def jwt_verifier(self):
        """Lazy load JWT verifier."""
        if self._jwt_verifier is None:
            self._jwt_verifier = get_jwt_verifier()
        return self._jwt_verifier

    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (no auth required).

        Args:
            path: Request path

        Returns:
            True if public path
        """
        if path in self.PUBLIC_PATHS:
            return True

        for prefix in self.PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return True

        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Verify authentication for protected routes.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            Response: HTTP response
        """
        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # API Key authentication for /v1/pipeline paths (GAS automation)
        if request.url.path.startswith("/v1/pipeline"):
            api_key = request.headers.get("X-API-Key")
            if api_key:
                settings = get_settings()
                if settings.GAS_API_KEY and hmac.compare_digest(api_key, settings.GAS_API_KEY):
                    request.state.user_id = "gas-automation"
                    request.state.user_email = None
                    request.state.user_role = "automation"
                    logger.debug(
                        "api_key_authenticated",
                        path=request.url.path,
                    )
                    return await call_next(request)
                else:
                    logger.warning(
                        "invalid_api_key",
                        path=request.url.path,
                    )
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "error": "Unauthorized",
                            "message": "Invalid API key",
                        },
                    )

        # Skip authentication if disabled
        if not self.require_auth:
            request.state.user_id = "anonymous"
            request.state.user_email = None
            request.state.user_role = "viewer"
            return await call_next(request)

        # Extract authorization header
        auth_header = request.headers.get("Authorization")
        request_id = getattr(request.state, "request_id", "unknown")

        if not auth_header:
            logger.warning(
                "missing_authentication",
                path=request.url.path,
                request_id=request_id,
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Unauthorized",
                    "message": "Authentication required",
                    "request_id": request_id,
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract token from header
        try:
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                raise ValueError("Invalid authorization header format")
            token = parts[1]
        except ValueError as e:
            logger.warning(
                "invalid_auth_header",
                path=request.url.path,
                request_id=request_id,
                error=str(e),
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Unauthorized",
                    "message": "Invalid authorization header format",
                    "request_id": request_id,
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify JWT token
        payload = self.jwt_verifier.verify_token(token)

        if not payload:
            logger.warning(
                "invalid_token",
                path=request.url.path,
                request_id=request_id,
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Unauthorized",
                    "message": "Invalid or expired token",
                    "request_id": request_id,
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Set user info on request state
        request.state.user_id = payload.get("sub")
        request.state.user_email = payload.get("email")
        request.state.user_role = (
            payload.get("app_metadata", {}).get("role")
            or payload.get("user_metadata", {}).get("role")
            or "editor"
        )

        logger.debug(
            "authenticated_request",
            path=request.url.path,
            user_id=request.state.user_id,
            user_email=request.state.user_email,
            user_role=request.state.user_role,
            request_id=request_id,
        )

        return await call_next(request)


def get_current_user_id(request: Request) -> Optional[str]:
    """Get current user ID from request state.

    Args:
        request: FastAPI request

    Returns:
        User ID if authenticated, None otherwise
    """
    return getattr(request.state, "user_id", None)


def get_current_user_email(request: Request) -> Optional[str]:
    """Get current user email from request state.

    Args:
        request: FastAPI request

    Returns:
        User email if authenticated, None otherwise
    """
    return getattr(request.state, "user_email", None)


def get_current_user_role(request: Request) -> Optional[str]:
    """Get current user role from request state.

    Args:
        request: FastAPI request

    Returns:
        User role if authenticated, None otherwise
    """
    return getattr(request.state, "user_role", None)
