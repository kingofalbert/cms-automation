"""CMS authentication handling."""

import base64
from typing import Any

import httpx

from src.config.logging import get_logger

logger = get_logger(__name__)


class WordPressAuth:
    """WordPress application password authentication."""

    def __init__(self, username: str, application_password: str) -> None:
        """Initialize WordPress authentication.

        Args:
            username: WordPress username
            application_password: WordPress application password
        """
        self.username = username
        self.application_password = application_password

    def get_headers(self) -> dict[str, str]:
        """Get authentication headers for WordPress REST API.

        Returns:
            dict: HTTP headers with Basic auth
        """
        # Create Basic auth credentials
        credentials = f"{self.username}:{self.application_password}"
        encoded = base64.b64encode(credentials.encode()).decode()

        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json",
        }


class TokenAuth:
    """Generic token-based authentication for CMS platforms."""

    def __init__(self, api_token: str, token_type: str = "Bearer") -> None:
        """Initialize token authentication.

        Args:
            api_token: API token
            token_type: Token type (Bearer, Token, API-Key, etc.)
        """
        self.api_token = api_token
        self.token_type = token_type

    def get_headers(self) -> dict[str, str]:
        """Get authentication headers.

        Returns:
            dict: HTTP headers with token auth
        """
        return {
            "Authorization": f"{self.token_type} {self.api_token}",
            "Content-Type": "application/json",
        }


class CMSAuthHandler:
    """Centralized CMS authentication handler."""

    def __init__(
        self,
        cms_type: str,
        base_url: str,
        credentials: dict[str, str],
        http_auth: tuple[str, str] | None = None,
    ) -> None:
        """Initialize CMS authentication handler.

        Args:
            cms_type: CMS platform type (wordpress, strapi, etc.)
            base_url: CMS base URL
            credentials: Authentication credentials
            http_auth: Optional HTTP Basic Auth tuple (username, password) for site-level auth
        """
        self.cms_type = cms_type.lower()
        self.base_url = base_url
        self.credentials = credentials
        self.http_auth = http_auth
        self._auth_handler = self._create_auth_handler()

    def _create_auth_handler(self) -> WordPressAuth | TokenAuth:
        """Create appropriate auth handler based on CMS type.

        Returns:
            Auth handler instance

        Raises:
            ValueError: If CMS type is not supported
        """
        if self.cms_type == "wordpress":
            username = self.credentials.get("username", "")
            password = self.credentials.get("application_password", "")
            return WordPressAuth(username, password)

        elif self.cms_type in ["strapi", "contentful", "ghost"]:
            api_token = self.credentials.get("api_token", "")
            return TokenAuth(api_token)

        else:
            raise ValueError(f"Unsupported CMS type: {self.cms_type}")

    def get_headers(self) -> dict[str, str]:
        """Get authentication headers for requests.

        Returns:
            dict: HTTP headers with authentication
        """
        return self._auth_handler.get_headers()

    async def verify_auth(self) -> bool:
        """Verify authentication is working.

        Returns:
            bool: True if authentication successful

        Raises:
            Exception: If authentication verification fails
        """
        headers = self.get_headers()

        try:
            # Create auth tuple for HTTP Basic Auth if provided
            auth = self.http_auth if self.http_auth else None

            async with httpx.AsyncClient() as client:
                # Try to access a basic endpoint to verify auth
                if self.cms_type == "wordpress":
                    url = f"{self.base_url}/wp-json/wp/v2/users/me"
                elif self.cms_type == "strapi":
                    url = f"{self.base_url}/api/users/me"
                else:
                    url = f"{self.base_url}/api/user"

                response = await client.get(url, headers=headers, auth=auth, timeout=10.0)

                if response.status_code == 200:
                    logger.info(
                        "cms_auth_verified",
                        cms_type=self.cms_type,
                        base_url=self.base_url,
                    )
                    return True
                else:
                    logger.error(
                        "cms_auth_failed",
                        cms_type=self.cms_type,
                        status_code=response.status_code,
                        response=response.text,
                    )
                    return False

        except Exception as e:
            logger.error(
                "cms_auth_error",
                cms_type=self.cms_type,
                error=str(e),
                exc_info=True,
            )
            raise
