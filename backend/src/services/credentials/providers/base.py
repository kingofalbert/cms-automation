"""Base credential provider interface."""

from abc import ABC, abstractmethod
from typing import Dict, Optional


class CredentialProvider(ABC):
    """Abstract base class for credential providers.

    All credential providers must implement this interface.
    """

    @abstractmethod
    async def get_credential(self, key: str) -> Optional[str]:
        """Get a credential by key.

        Args:
            key: The credential key to retrieve

        Returns:
            The credential value, or None if not found

        Raises:
            RuntimeError: If credential retrieval fails
        """
        pass

    @abstractmethod
    async def list_credentials(self) -> Dict[str, str]:
        """List all available credentials.

        Returns:
            Dictionary of all credentials (key -> value)

        Raises:
            RuntimeError: If listing credentials fails
        """
        pass

    @abstractmethod
    async def set_credential(self, key: str, value: str) -> bool:
        """Set or update a credential.

        Args:
            key: The credential key
            value: The credential value

        Returns:
            True if successful, False otherwise

        Raises:
            RuntimeError: If setting credential fails
        """
        pass

    @abstractmethod
    async def delete_credential(self, key: str) -> bool:
        """Delete a credential.

        Args:
            key: The credential key to delete

        Returns:
            True if successful, False otherwise

        Raises:
            RuntimeError: If deleting credential fails
        """
        pass
