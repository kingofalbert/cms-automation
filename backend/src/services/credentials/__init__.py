"""Credential management services."""

from src.services.credentials.manager import CredentialManager, get_credential_manager
from src.services.credentials.providers.base import CredentialProvider
from src.services.credentials.providers.env_file import EnvFileProvider

# Optional imports (may not be available if dependencies not installed)
try:
    from src.services.credentials.providers.aws_secrets import (
        AWSSecretsManagerProvider,
    )

    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

try:
    from src.services.credentials.providers.gcp_secrets import (
        GCPSecretManagerProvider,
    )

    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False

__all__ = [
    "CredentialManager",
    "CredentialProvider",
    "EnvFileProvider",
    "get_credential_manager",
]

# Add optional exports if available
if AWS_AVAILABLE:
    __all__.append("AWSSecretsManagerProvider")

if GCP_AVAILABLE:
    __all__.append("GCPSecretManagerProvider")
