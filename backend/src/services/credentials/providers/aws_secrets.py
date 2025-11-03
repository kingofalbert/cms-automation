"""AWS Secrets Manager credential provider."""

import json
from typing import Dict, Optional

from src.config.logging import get_logger
from src.services.credentials.providers.base import CredentialProvider

logger = get_logger(__name__)

try:
    import boto3
    from botocore.exceptions import ClientError

    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning(
        "boto3_not_installed",
        message="boto3 not installed, AWS Secrets Manager provider unavailable",
    )


class AWSSecretsManagerProvider(CredentialProvider):
    """Provider that reads credentials from AWS Secrets Manager.

    This provider is suitable for production environments where
    credentials need to be stored securely in the cloud.

    **Requirements**:
    - boto3 package installed (`pip install boto3`)
    - AWS credentials configured (IAM role, environment variables, or ~/.aws/credentials)
    - IAM permissions: `secretsmanager:GetSecretValue`, `secretsmanager:PutSecretValue`

    **Credentials Format**:
    The secret in AWS Secrets Manager must be a JSON object with key-value pairs:
    ```json
    {
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "CMS_APPLICATION_PASSWORD": "password123",
        "DATABASE_PASSWORD": "dbpass"
    }
    ```
    """

    def __init__(self, secret_name: str, region: str = "us-east-1"):
        """Initialize the AWS Secrets Manager provider.

        Args:
            secret_name: Name or ARN of the secret in AWS Secrets Manager
            region: AWS region (default: us-east-1)

        Raises:
            RuntimeError: If boto3 is not installed
        """
        if not BOTO3_AVAILABLE:
            raise RuntimeError(
                "boto3 is required for AWS Secrets Manager provider. "
                "Install it with: pip install boto3"
            )

        self.secret_name = secret_name
        self.region = region
        self.client = boto3.client("secretsmanager", region_name=region)
        self._secrets: Optional[Dict[str, str]] = None

        logger.info(
            "aws_secrets_manager_initialized",
            secret_name=secret_name,
            region=region,
        )

    async def _load_secrets(self, force_reload: bool = False):
        """Load all secrets from AWS Secrets Manager.

        Args:
            force_reload: Force reload even if secrets are already cached

        Raises:
            RuntimeError: If loading secrets fails
        """
        if self._secrets is not None and not force_reload:
            return

        try:
            logger.debug(
                "loading_secrets_from_aws",
                secret_name=self.secret_name,
                force_reload=force_reload,
            )

            response = self.client.get_secret_value(SecretId=self.secret_name)

            # Parse the secret string as JSON
            self._secrets = json.loads(response["SecretString"])

            logger.info(
                "secrets_loaded_from_aws",
                secret_name=self.secret_name,
                secret_count=len(self._secrets),
            )

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = e.response["Error"]["Message"]

            logger.error(
                "aws_secrets_load_failed",
                secret_name=self.secret_name,
                error_code=error_code,
                error_message=error_msg,
                exc_info=True,
            )

            raise RuntimeError(
                f"Failed to load secrets from AWS Secrets Manager: {error_code} - {error_msg}"
            ) from e

        except json.JSONDecodeError as e:
            logger.error(
                "aws_secrets_invalid_json",
                secret_name=self.secret_name,
                error=str(e),
                exc_info=True,
            )

            raise RuntimeError(
                f"Secret '{self.secret_name}' is not valid JSON. "
                "Secrets must be stored as JSON key-value pairs."
            ) from e

    async def get_credential(self, key: str) -> Optional[str]:
        """Get credential from AWS Secrets Manager.

        Args:
            key: The credential key

        Returns:
            The credential value, or None if not found

        Raises:
            RuntimeError: If loading secrets fails
        """
        await self._load_secrets()

        value = self._secrets.get(key)

        if value:
            logger.debug(
                "credential_retrieved",
                key=key,
                source="aws_secrets_manager",
                found=True,
            )
        else:
            logger.debug(
                "credential_not_found",
                key=key,
                source="aws_secrets_manager",
                found=False,
            )

        return value

    async def list_credentials(self) -> Dict[str, str]:
        """List all credentials from AWS Secrets Manager.

        Returns:
            Dictionary of all credentials (key -> value)

        Raises:
            RuntimeError: If loading secrets fails
        """
        await self._load_secrets()

        logger.debug(
            "listing_all_credentials",
            source="aws_secrets_manager",
            count=len(self._secrets),
        )

        return self._secrets.copy()

    async def set_credential(self, key: str, value: str) -> bool:
        """Update credential in AWS Secrets Manager.

        This updates a single key-value pair within the secret.

        Args:
            key: The credential key
            value: The credential value

        Returns:
            True if successful, False otherwise

        Raises:
            RuntimeError: If loading or updating secrets fails
        """
        await self._load_secrets()

        # Update the local cache
        self._secrets[key] = value

        try:
            logger.info(
                "updating_credential_in_aws",
                key=key,
                secret_name=self.secret_name,
            )

            # Update the entire secret with the new value
            self.client.update_secret(
                SecretId=self.secret_name, SecretString=json.dumps(self._secrets)
            )

            logger.info(
                "credential_updated_in_aws",
                key=key,
                secret_name=self.secret_name,
                success=True,
            )

            return True

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = e.response["Error"]["Message"]

            logger.error(
                "aws_credential_update_failed",
                key=key,
                secret_name=self.secret_name,
                error_code=error_code,
                error_message=error_msg,
                exc_info=True,
            )

            # Reload secrets to ensure cache is in sync
            await self._load_secrets(force_reload=True)

            return False

    async def delete_credential(self, key: str) -> bool:
        """Delete credential from AWS Secrets Manager.

        This removes a single key-value pair from the secret.

        Args:
            key: The credential key to delete

        Returns:
            True if successful, False otherwise

        Raises:
            RuntimeError: If loading or updating secrets fails
        """
        await self._load_secrets()

        if key not in self._secrets:
            logger.warning(
                "credential_delete_failed",
                key=key,
                secret_name=self.secret_name,
                reason="Key not found in secret",
            )
            return False

        # Remove from local cache
        del self._secrets[key]

        try:
            logger.info(
                "deleting_credential_from_aws",
                key=key,
                secret_name=self.secret_name,
            )

            # Update the entire secret without the deleted key
            self.client.update_secret(
                SecretId=self.secret_name, SecretString=json.dumps(self._secrets)
            )

            logger.info(
                "credential_deleted_from_aws",
                key=key,
                secret_name=self.secret_name,
                success=True,
            )

            return True

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = e.response["Error"]["Message"]

            logger.error(
                "aws_credential_delete_failed",
                key=key,
                secret_name=self.secret_name,
                error_code=error_code,
                error_message=error_msg,
                exc_info=True,
            )

            # Reload secrets to ensure cache is in sync
            await self._load_secrets(force_reload=True)

            return False
