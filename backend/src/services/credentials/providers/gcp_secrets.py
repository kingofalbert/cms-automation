"""Google Cloud Secret Manager credential provider."""

from typing import Dict, Optional

from src.config.logging import get_logger
from src.services.credentials.providers.base import CredentialProvider

logger = get_logger(__name__)

try:
    from google.cloud import secretmanager
    from google.api_core import exceptions as gcp_exceptions

    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False
    logger.warning(
        "gcp_secret_manager_not_installed",
        message="google-cloud-secret-manager not installed, GCP provider unavailable",
    )


class GCPSecretManagerProvider(CredentialProvider):
    """Provider that reads credentials from Google Cloud Secret Manager.

    This provider is suitable for production environments where
    credentials need to be stored securely in Google Cloud.

    **Requirements**:
    - google-cloud-secret-manager package installed
    - GCP credentials configured (service account, ADC, or environment)
    - IAM permissions: `secretmanager.versions.access`, `secretmanager.secrets.create`

    **Credentials Format**:
    Each credential is stored as a separate secret in GCP Secret Manager.

    **Secret Naming Convention**:
    - Project: your-gcp-project
    - Secret name: ANTHROPIC_API_KEY
    - Full path: projects/your-gcp-project/secrets/ANTHROPIC_API_KEY/versions/latest

    **Cost**: ~$0.06 per 10,000 accesses (much cheaper than AWS)
    """

    def __init__(self, project_id: str, secret_prefix: str = ""):
        """Initialize the GCP Secret Manager provider.

        Args:
            project_id: GCP project ID
            secret_prefix: Optional prefix for secret names (e.g., "cms-automation-")

        Raises:
            RuntimeError: If google-cloud-secret-manager is not installed
        """
        if not GCP_AVAILABLE:
            raise RuntimeError(
                "google-cloud-secret-manager is required for GCP Secret Manager provider. "
                "Install it with: pip install google-cloud-secret-manager"
            )

        self.project_id = project_id
        self.secret_prefix = secret_prefix
        self.client = secretmanager.SecretManagerServiceClient()

        # Cache for secrets
        self._secrets_cache: Dict[str, str] = {}

        logger.info(
            "gcp_secret_manager_initialized",
            project_id=project_id,
            secret_prefix=secret_prefix or "(none)",
        )

    def _get_secret_name(self, key: str) -> str:
        """Get full secret name with prefix.

        Args:
            key: The credential key

        Returns:
            Full secret name (e.g., "cms-automation-ANTHROPIC_API_KEY")
        """
        return f"{self.secret_prefix}{key}" if self.secret_prefix else key

    def _get_secret_path(self, key: str) -> str:
        """Get full secret path for GCP API.

        Args:
            key: The credential key

        Returns:
            Full secret path (e.g., "projects/123/secrets/ANTHROPIC_API_KEY/versions/latest")
        """
        secret_name = self._get_secret_name(key)
        return f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"

    async def get_credential(self, key: str) -> Optional[str]:
        """Get credential from GCP Secret Manager.

        Args:
            key: The credential key

        Returns:
            The credential value, or None if not found

        Raises:
            RuntimeError: If accessing secret fails (other than NotFound)
        """
        # Check cache first
        if key in self._secrets_cache:
            logger.debug(
                "credential_from_cache",
                key=key,
                source="gcp_secret_manager",
            )
            return self._secrets_cache[key]

        try:
            secret_path = self._get_secret_path(key)

            logger.debug(
                "accessing_gcp_secret",
                key=key,
                secret_path=secret_path,
            )

            # Access the secret version
            response = self.client.access_secret_version(request={"name": secret_path})

            # Decode the secret data
            value = response.payload.data.decode("UTF-8")

            # Cache the value
            self._secrets_cache[key] = value

            logger.debug(
                "credential_retrieved",
                key=key,
                source="gcp_secret_manager",
                found=True,
            )

            return value

        except gcp_exceptions.NotFound:
            logger.debug(
                "credential_not_found",
                key=key,
                source="gcp_secret_manager",
                found=False,
            )
            return None

        except gcp_exceptions.PermissionDenied as e:
            logger.error(
                "gcp_permission_denied",
                key=key,
                error=str(e),
                message="Check IAM permissions: secretmanager.versions.access",
                exc_info=True,
            )
            raise RuntimeError(
                f"Permission denied accessing secret '{key}'. "
                f"Ensure service account has 'secretmanager.versions.access' permission."
            ) from e

        except Exception as e:
            logger.error(
                "gcp_secret_access_failed",
                key=key,
                error=str(e),
                exc_info=True,
            )
            raise RuntimeError(
                f"Failed to access GCP secret '{key}': {str(e)}"
            ) from e

    async def list_credentials(self) -> Dict[str, str]:
        """List all credentials from GCP Secret Manager.

        This lists all secrets in the project and retrieves their values.

        Returns:
            Dictionary of all credentials (key -> value)

        Raises:
            RuntimeError: If listing secrets fails

        Warning:
            This method makes one API call per secret, which can be expensive
            if you have many secrets. Use sparingly.
        """
        try:
            parent = f"projects/{self.project_id}"

            logger.debug(
                "listing_gcp_secrets",
                project_id=self.project_id,
            )

            # List all secrets
            secrets = self.client.list_secrets(request={"parent": parent})

            credentials = {}

            for secret in secrets:
                # Extract secret name from full path
                # Format: projects/123/secrets/SECRET_NAME
                secret_name = secret.name.split("/")[-1]

                # Remove prefix if present
                if self.secret_prefix and secret_name.startswith(self.secret_prefix):
                    key = secret_name[len(self.secret_prefix) :]
                else:
                    key = secret_name

                # Get the secret value
                value = await self.get_credential(key)
                if value:
                    credentials[key] = value

            logger.info(
                "credentials_listed",
                source="gcp_secret_manager",
                count=len(credentials),
            )

            return credentials

        except gcp_exceptions.PermissionDenied as e:
            logger.error(
                "gcp_permission_denied",
                error=str(e),
                message="Check IAM permissions: secretmanager.secrets.list",
                exc_info=True,
            )
            raise RuntimeError(
                "Permission denied listing secrets. "
                "Ensure service account has 'secretmanager.secrets.list' permission."
            ) from e

        except Exception as e:
            logger.error(
                "gcp_secrets_list_failed",
                error=str(e),
                exc_info=True,
            )
            raise RuntimeError(f"Failed to list GCP secrets: {str(e)}") from e

    async def set_credential(self, key: str, value: str) -> bool:
        """Create or update a credential in GCP Secret Manager.

        This creates a new secret version with the provided value.

        Args:
            key: The credential key
            value: The credential value

        Returns:
            True if successful, False otherwise

        Raises:
            RuntimeError: If creating/updating secret fails
        """
        try:
            parent = f"projects/{self.project_id}"
            secret_name = self._get_secret_name(key)
            secret_id = f"{parent}/secrets/{secret_name}"

            logger.info(
                "updating_gcp_secret",
                key=key,
                secret_name=secret_name,
            )

            # Try to create the secret first (in case it doesn't exist)
            try:
                self.client.create_secret(
                    request={
                        "parent": parent,
                        "secret_id": secret_name,
                        "secret": {
                            "replication": {"automatic": {}},
                        },
                    }
                )
                logger.info(
                    "gcp_secret_created",
                    key=key,
                    secret_name=secret_name,
                )
            except gcp_exceptions.AlreadyExists:
                # Secret already exists, we'll just add a new version
                logger.debug(
                    "gcp_secret_exists",
                    key=key,
                    message="Secret already exists, adding new version",
                )

            # Add a new secret version with the value
            self.client.add_secret_version(
                request={
                    "parent": secret_id,
                    "payload": {"data": value.encode("UTF-8")},
                }
            )

            # Invalidate cache
            if key in self._secrets_cache:
                del self._secrets_cache[key]

            logger.info(
                "credential_updated_in_gcp",
                key=key,
                secret_name=secret_name,
                success=True,
            )

            return True

        except gcp_exceptions.PermissionDenied as e:
            logger.error(
                "gcp_permission_denied",
                key=key,
                error=str(e),
                message="Check IAM permissions: secretmanager.secrets.create, secretmanager.versions.add",
                exc_info=True,
            )
            return False

        except Exception as e:
            logger.error(
                "gcp_secret_update_failed",
                key=key,
                error=str(e),
                exc_info=True,
            )
            return False

    async def delete_credential(self, key: str) -> bool:
        """Delete a credential from GCP Secret Manager.

        This deletes the entire secret (all versions).

        Args:
            key: The credential key to delete

        Returns:
            True if successful, False otherwise

        Raises:
            RuntimeError: If deleting secret fails

        Warning:
            This permanently deletes the secret and all its versions.
            Use with caution.
        """
        try:
            secret_name = self._get_secret_name(key)
            secret_path = f"projects/{self.project_id}/secrets/{secret_name}"

            logger.info(
                "deleting_gcp_secret",
                key=key,
                secret_name=secret_name,
            )

            # Delete the secret
            self.client.delete_secret(request={"name": secret_path})

            # Remove from cache
            if key in self._secrets_cache:
                del self._secrets_cache[key]

            logger.info(
                "credential_deleted_from_gcp",
                key=key,
                secret_name=secret_name,
                success=True,
            )

            return True

        except gcp_exceptions.NotFound:
            logger.warning(
                "credential_delete_failed",
                key=key,
                reason="Secret not found",
            )
            return False

        except gcp_exceptions.PermissionDenied as e:
            logger.error(
                "gcp_permission_denied",
                key=key,
                error=str(e),
                message="Check IAM permissions: secretmanager.secrets.delete",
                exc_info=True,
            )
            return False

        except Exception as e:
            logger.error(
                "gcp_secret_delete_failed",
                key=key,
                error=str(e),
                exc_info=True,
            )
            return False

    def clear_cache(self):
        """Clear the internal secrets cache."""
        cache_size = len(self._secrets_cache)
        self._secrets_cache.clear()

        logger.info(
            "gcp_cache_cleared",
            credentials_cleared=cache_size,
        )
