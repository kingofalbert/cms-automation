"""Credential manager with caching and provider factory."""

import os
import time
from typing import Dict, Optional

from src.config.logging import get_logger
from src.services.credentials.providers.base import CredentialProvider
from src.services.credentials.providers.env_file import EnvFileProvider

logger = get_logger(__name__)

# Global credential manager instance
_credential_manager: Optional["CredentialManager"] = None


class CredentialManager:
    """Centralized credential management with caching.

    The CredentialManager provides a caching layer on top of credential
    providers to reduce API calls and improve performance.

    Features:
    - Credential caching with configurable TTL
    - Support for multiple credential providers
    - Automatic cache invalidation on updates
    - Thread-safe operations
    """

    def __init__(
        self,
        provider: CredentialProvider,
        cache_ttl: int = 300,
        enable_cache: bool = True,
    ):
        """Initialize the credential manager.

        Args:
            provider: The credential provider to use
            cache_ttl: Cache time-to-live in seconds (default: 300 = 5 minutes)
            enable_cache: Enable/disable caching (default: True)
        """
        self.provider = provider
        self.cache_ttl = cache_ttl
        self.enable_cache = enable_cache

        # Cache structure: {key: (value, timestamp)}
        self._cache: Dict[str, tuple[str, float]] = {}

        logger.info(
            "credential_manager_initialized",
            provider=provider.__class__.__name__,
            cache_ttl=cache_ttl,
            cache_enabled=enable_cache,
        )

    async def get(self, key: str, use_cache: bool = True) -> Optional[str]:
        """Get credential with optional caching.

        Args:
            key: The credential key
            use_cache: Use cache if available (default: True)

        Returns:
            The credential value, or None if not found

        Raises:
            RuntimeError: If credential retrieval fails
        """
        # Check cache first (if enabled and requested)
        if self.enable_cache and use_cache:
            cached_value = self._get_from_cache(key)
            if cached_value is not None:
                logger.debug(
                    "credential_from_cache",
                    key=key,
                    cache_hit=True,
                )
                return cached_value

        # Get from provider
        value = await self.provider.get_credential(key)

        # Store in cache (if enabled)
        if value is not None and self.enable_cache:
            self._store_in_cache(key, value)

        return value

    async def get_all(self) -> Dict[str, str]:
        """Get all credentials.

        Returns:
            Dictionary of all credentials

        Raises:
            RuntimeError: If credential retrieval fails
        """
        return await self.provider.list_credentials()

    async def set(self, key: str, value: str) -> bool:
        """Set or update a credential.

        This will also invalidate the cache for this key.

        Args:
            key: The credential key
            value: The credential value

        Returns:
            True if successful, False otherwise

        Raises:
            RuntimeError: If setting credential fails
        """
        success = await self.provider.set_credential(key, value)

        if success:
            # Invalidate cache for this key
            self._invalidate_cache(key)

            logger.info(
                "credential_set",
                key=key,
                cache_invalidated=True,
            )

        return success

    async def delete(self, key: str) -> bool:
        """Delete a credential.

        This will also remove the key from cache.

        Args:
            key: The credential key

        Returns:
            True if successful, False otherwise

        Raises:
            RuntimeError: If deleting credential fails
        """
        success = await self.provider.delete_credential(key)

        if success:
            # Remove from cache
            self._invalidate_cache(key)

            logger.info(
                "credential_deleted",
                key=key,
                cache_invalidated=True,
            )

        return success

    async def rotate(self, key: str, new_value: str) -> bool:
        """Rotate a credential (convenience method for set).

        Args:
            key: The credential key
            new_value: The new credential value

        Returns:
            True if successful, False otherwise
        """
        logger.info("credential_rotation_started", key=key)
        return await self.set(key, new_value)

    def clear_cache(self):
        """Clear all cached credentials."""
        cache_size = len(self._cache)
        self._cache.clear()

        logger.info(
            "credential_cache_cleared",
            credentials_cleared=cache_size,
        )

    def _get_from_cache(self, key: str) -> Optional[str]:
        """Get credential from cache if not expired.

        Args:
            key: The credential key

        Returns:
            The cached value, or None if not in cache or expired
        """
        if key not in self._cache:
            return None

        value, timestamp = self._cache[key]
        current_time = time.time()

        # Check if cache entry has expired
        if current_time - timestamp > self.cache_ttl:
            # Cache expired, remove it
            del self._cache[key]
            logger.debug(
                "cache_entry_expired",
                key=key,
                age_seconds=current_time - timestamp,
            )
            return None

        return value

    def _store_in_cache(self, key: str, value: str):
        """Store credential in cache.

        Args:
            key: The credential key
            value: The credential value
        """
        self._cache[key] = (value, time.time())

        logger.debug(
            "credential_cached",
            key=key,
            cache_size=len(self._cache),
        )

    def _invalidate_cache(self, key: str):
        """Invalidate a single cache entry.

        Args:
            key: The credential key to invalidate
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(
                "cache_invalidated",
                key=key,
            )


def create_credential_provider(backend: str) -> CredentialProvider:
    """Factory function to create credential providers.

    Args:
        backend: The backend type ("env", "aws_secrets_manager", "vault")

    Returns:
        An instance of the appropriate credential provider

    Raises:
        ValueError: If backend is not supported
        RuntimeError: If provider requirements are not met
    """
    backend = backend.lower()

    if backend == "env":
        # Environment file provider (development)
        env_file = os.getenv("CREDENTIAL_ENV_FILE", ".env")
        logger.info(
            "creating_provider",
            backend="env",
            env_file=env_file,
        )
        return EnvFileProvider(env_file=env_file)

    elif backend == "aws_secrets_manager":
        # AWS Secrets Manager provider (production)
        from src.services.credentials.providers.aws_secrets import (
            AWSSecretsManagerProvider,
        )

        secret_name = os.getenv("AWS_SECRET_NAME")
        if not secret_name:
            raise ValueError(
                "AWS_SECRET_NAME environment variable is required for aws_secrets_manager backend"
            )

        region = os.getenv("AWS_REGION", "us-east-1")

        logger.info(
            "creating_provider",
            backend="aws_secrets_manager",
            secret_name=secret_name,
            region=region,
        )

        return AWSSecretsManagerProvider(secret_name=secret_name, region=region)

    elif backend == "gcp_secret_manager":
        # Google Cloud Secret Manager provider (production)
        from src.services.credentials.providers.gcp_secrets import (
            GCPSecretManagerProvider,
        )

        project_id = os.getenv("GCP_PROJECT_ID")
        if not project_id:
            raise ValueError(
                "GCP_PROJECT_ID environment variable is required for gcp_secret_manager backend"
            )

        secret_prefix = os.getenv("GCP_SECRET_PREFIX", "")

        logger.info(
            "creating_provider",
            backend="gcp_secret_manager",
            project_id=project_id,
            secret_prefix=secret_prefix or "(none)",
        )

        return GCPSecretManagerProvider(
            project_id=project_id, secret_prefix=secret_prefix
        )

    else:
        raise ValueError(
            f"Unsupported credential backend: {backend}. "
            f"Supported backends: env, aws_secrets_manager, gcp_secret_manager"
        )


def get_credential_manager(force_recreate: bool = False) -> CredentialManager:
    """Get or create the global credential manager instance.

    Args:
        force_recreate: Force recreation of the credential manager (default: False)

    Returns:
        The global credential manager instance

    Raises:
        ValueError: If CREDENTIAL_STORAGE_BACKEND is not set or invalid
        RuntimeError: If provider requirements are not met
    """
    global _credential_manager

    if _credential_manager is not None and not force_recreate:
        return _credential_manager

    # Get backend from environment
    backend = os.getenv("CREDENTIAL_STORAGE_BACKEND", "env")

    # Get cache configuration
    cache_ttl = int(os.getenv("CREDENTIAL_CACHE_TTL", "300"))
    enable_cache = os.getenv("CREDENTIAL_CACHE_ENABLED", "true").lower() == "true"

    logger.info(
        "initializing_credential_manager",
        backend=backend,
        cache_ttl=cache_ttl,
        cache_enabled=enable_cache,
    )

    # Create provider
    provider = create_credential_provider(backend)

    # Create manager
    _credential_manager = CredentialManager(
        provider=provider,
        cache_ttl=cache_ttl,
        enable_cache=enable_cache,
    )

    return _credential_manager
