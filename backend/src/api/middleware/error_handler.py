"""Error handling middleware for FastAPI."""

import traceback
import uuid
from collections.abc import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.config.logging import get_logger

logger = get_logger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling and logging."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response | JSONResponse:
        """Process request and handle errors.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            Response: HTTP response
        """
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

        except ValueError as exc:
            # Validation errors
            logger.warning(
                "validation_error",
                request_id=request_id,
                path=request.url.path,
                error=str(exc),
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Validation Error",
                    "message": str(exc),
                    "request_id": request_id,
                },
                headers={"X-Request-ID": request_id},
            )

        except PermissionError as exc:
            # Authorization errors
            logger.warning(
                "permission_error",
                request_id=request_id,
                path=request.url.path,
                error=str(exc),
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Permission Denied",
                    "message": str(exc),
                    "request_id": request_id,
                },
                headers={"X-Request-ID": request_id},
            )

        except FileNotFoundError as exc:
            # Not found errors
            logger.info(
                "not_found_error",
                request_id=request_id,
                path=request.url.path,
                error=str(exc),
            )
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": "Not Found",
                    "message": str(exc),
                    "request_id": request_id,
                },
                headers={"X-Request-ID": request_id},
            )

        except Exception as exc:
            # Unexpected errors
            tb = traceback.format_exc()
            logger.error(
                "unexpected_error",
                request_id=request_id,
                path=request.url.path,
                error=str(exc),
                traceback=tb,
                exc_info=True,
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                    "request_id": request_id,
                },
                headers={"X-Request-ID": request_id},
            )
