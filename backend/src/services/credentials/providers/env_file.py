"""Environment file credential provider."""

import os
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv

from src.config.logging import get_logger
from src.services.credentials.providers.base import CredentialProvider

logger = get_logger(__name__)


class EnvFileProvider(CredentialProvider):
    """Provider that reads credentials from .env file.

    This provider is suitable for development environments where
    credentials are stored in a local .env file.

    **Security Warning**: This provider stores credentials in plaintext
    and should NOT be used in production environments.
    """

    def __init__(self, env_file: str = ".env"):
        """Initialize the environment file provider.

        Args:
            env_file: Path to the .env file (default: .env)
        """
        self.env_file = Path(env_file)

        # Load environment variables from file
        if self.env_file.exists():
            load_dotenv(self.env_file)
            logger.info(
                "env_file_loaded",
                env_file=str(self.env_file),
                exists=True,
            )
        else:
            logger.warning(
                "env_file_not_found",
                env_file=str(self.env_file),
                message="Env file does not exist, using system environment only",
            )

    async def get_credential(self, key: str) -> Optional[str]:
        """Get credential from environment.

        Args:
            key: Environment variable name

        Returns:
            The credential value, or None if not found
        """
        value = os.getenv(key)

        if value:
            logger.debug(
                "credential_retrieved",
                key=key,
                source="env_file",
                found=True,
            )
        else:
            logger.debug(
                "credential_not_found",
                key=key,
                source="env_file",
                found=False,
            )

        return value

    async def list_credentials(self) -> Dict[str, str]:
        """List all environment variables.

        Returns:
            Dictionary of all environment variables

        Note:
            This returns ALL environment variables, not just those
            from the .env file. Use with caution.
        """
        logger.debug("listing_all_credentials", source="env_file")
        return dict(os.environ)

    async def set_credential(self, key: str, value: str) -> bool:
        """Set credential in environment (memory only).

        This sets the credential in the current process environment
        but does NOT persist it to the .env file.

        Args:
            key: Environment variable name
            value: Environment variable value

        Returns:
            Always returns True (setting env var always succeeds)
        """
        os.environ[key] = value

        logger.info(
            "credential_set",
            key=key,
            source="env_file",
            persisted=False,
            message="Credential set in memory only, not persisted to .env file",
        )

        return True

    async def delete_credential(self, key: str) -> bool:
        """Delete credential from environment (memory only).

        This removes the credential from the current process environment
        but does NOT modify the .env file.

        Args:
            key: Environment variable name

        Returns:
            True if the key existed and was deleted, False otherwise
        """
        if key in os.environ:
            del os.environ[key]
            logger.info(
                "credential_deleted",
                key=key,
                source="env_file",
                success=True,
            )
            return True
        else:
            logger.warning(
                "credential_delete_failed",
                key=key,
                source="env_file",
                reason="Key not found in environment",
            )
            return False
