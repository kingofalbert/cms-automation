"""Supabase JWT verification service.

Verifies JWT tokens issued by Supabase Auth using JWKS.
"""

import httpx
from functools import lru_cache
from typing import Any
from jose import jwt, JWTError, ExpiredSignatureError
from jose.exceptions import JWTClaimsError

from src.config.logging import get_logger
from src.config.settings import get_settings

logger = get_logger(__name__)


class SupabaseJWTVerifier:
    """Verifies Supabase JWT tokens using the JWT secret."""

    def __init__(
        self,
        supabase_url: str,
        jwt_secret: str,
        audience: str = "authenticated",
    ):
        """Initialize the JWT verifier.

        Args:
            supabase_url: Supabase project URL
            jwt_secret: JWT secret for verification (from Supabase dashboard)
            audience: Expected audience claim (default: "authenticated")
        """
        self.supabase_url = supabase_url.rstrip("/")
        self.jwt_secret = jwt_secret
        self.audience = audience
        self.issuer = f"{self.supabase_url}/auth/v1"
        self._jwks_cache: dict[str, Any] | None = None

    def verify_token(self, token: str) -> dict[str, Any] | None:
        """Verify a Supabase JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            # Decode and verify the token
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"],
                audience=self.audience,
                issuer=self.issuer,
            )

            logger.debug(
                "jwt_verified",
                user_id=payload.get("sub"),
                email=payload.get("email"),
            )

            return payload

        except ExpiredSignatureError:
            logger.warning("jwt_expired")
            return None

        except JWTClaimsError as e:
            logger.warning("jwt_claims_error", error=str(e))
            return None

        except JWTError as e:
            logger.warning("jwt_verification_failed", error=str(e))
            return None

        except Exception as e:
            logger.error("jwt_unexpected_error", error=str(e))
            return None

    def get_user_id(self, token: str) -> str | None:
        """Extract user ID from token.

        Args:
            token: JWT token string

        Returns:
            User ID (sub claim) if valid, None otherwise
        """
        payload = self.verify_token(token)
        return payload.get("sub") if payload else None

    def get_user_email(self, token: str) -> str | None:
        """Extract user email from token.

        Args:
            token: JWT token string

        Returns:
            User email if valid, None otherwise
        """
        payload = self.verify_token(token)
        return payload.get("email") if payload else None

    def get_user_role(self, token: str) -> str | None:
        """Extract user role from token metadata.

        Args:
            token: JWT token string

        Returns:
            User role from app_metadata if valid, None otherwise
        """
        payload = self.verify_token(token)
        if not payload:
            return None

        # Role might be in app_metadata or user_metadata
        app_metadata = payload.get("app_metadata", {})
        user_metadata = payload.get("user_metadata", {})

        return (
            app_metadata.get("role")
            or user_metadata.get("role")
            or "editor"  # Default role
        )


@lru_cache()
def get_jwt_verifier() -> SupabaseJWTVerifier:
    """Get the singleton JWT verifier instance.

    Returns:
        SupabaseJWTVerifier instance configured from settings
    """
    settings = get_settings()

    # Get Supabase settings
    supabase_url = getattr(settings, "SUPABASE_URL", None)
    jwt_secret = getattr(settings, "SUPABASE_JWT_SECRET", None)

    if not supabase_url:
        logger.warning("SUPABASE_URL not configured, using placeholder")
        supabase_url = "https://placeholder.supabase.co"

    if not jwt_secret:
        logger.warning("SUPABASE_JWT_SECRET not configured, JWT verification will fail")
        jwt_secret = "placeholder-secret"

    return SupabaseJWTVerifier(
        supabase_url=supabase_url,
        jwt_secret=jwt_secret,
    )
