from typing import Dict, Any, Literal, Optional, List, TYPE_CHECKING
import logging

from ..exceptions import (
    AuthenticationError,
    InvalidFieldError
)

if TYPE_CHECKING:
    from ..client import NoteDxClient

class KeyManager:
    """
    Handles API key management operations for the NoteDx API.
    
    This class provides methods for:

    - Creating and listing API keys
    - Managing key metadata
    - Updating key status
    - Key deletion
    """
    
    def __init__(self, client: "NoteDxClient") -> None:
        """
        Initialize the key manager.
        
        Args:
            client: The parent NoteDxClient instance
        """
        self._client = client
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.debug("Initialized KeyManager")

    def list_api_keys(self, show_full: bool = False) -> List[Dict[str, Any]]:
        """
        List all API keys associated with the account.

        ```bash
        GET /user/list-api-keys
        ```

        Args:
            show_full: If True, returns unmasked API keys. Default False for security.

        Returns:
            List of dicts, each containing:

            - key: API key value (masked unless show_full=True)
            - type: Key type ('sandbox' or 'live')
            - status: Current status ('active' or 'inactive')
            - created_at: Creation timestamp (ISO format)
            - last_used: Last usage timestamp (ISO format)
            - metadata: Key metadata (only for live keys)

        Raises:
            AuthenticationError: If authentication fails or missing user ID
            AuthorizationError: If not authorized to list keys
            NetworkError: If connection issues occur

        Note:
            - Keys are sorted with sandbox first, then live keys
            - Masked keys show only last 4 characters
            - Metadata is only present for live keys
        """
        params = {'showFull': 'true'} if show_full else None
        return self._client._request("GET", "user/list-api-keys", params=params)

    def create_api_key(
        self,
        key_type: Literal['sandbox', 'live'],
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new API key.

        ```bash
        POST /user/create-api-key
        ```

        Args:
            key_type: Type of key to create ('sandbox' or 'live')
            metadata: Optional metadata for live keys
                     Must be dict of string key-value pairs
                     Keys <= 50 chars, values <= 200 chars
                     Cannot contain sensitive keywords

        Returns:
            Dict containing:

            - api_key: The full API key value (only shown once)
            - key_type: Type of key created
            - metadata: Provided metadata (live keys only)

        Raises:
            AuthenticationError: If authentication fails or missing user ID
            AuthorizationError: If not authorized to create keys
            BadRequestError: If invalid JSON format in request
            ValidationError: If key_type or metadata is invalid
            PaymentRequiredError: If account has payment issues
            NetworkError: If connection issues occur

        Note:
            - Save the api_key value immediately - it cannot be retrieved later
            - Only one sandbox key allowed per account
            - Metadata only supported for live keys
            - Cannot create live keys if account is cancelled
            - First live key activates the account
        """
        data = {
            'keyType': key_type,
            'metadata': metadata
        }
        return self._client._request("POST", "user/create-api-key", data=data)

    def update_metadata(
        self,
        api_key: str,
        metadata: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Update metadata for a live API key.

        ```bash
        POST /user/update-api-key-metadata
        ```

        Args:
            api_key: The API key to update
            metadata: New metadata dictionary
                     Must be dict of string key-value pairs
                     Keys <= 50 chars, values <= 200 chars
                     Cannot contain sensitive keywords

        Returns:
            Dict containing:

            - message: "API key metadata updated successfully"
            - api_key: Updated key identifier

        Raises:
            AuthenticationError: If authentication fails or missing user ID
            AuthorizationError: If not authorized to modify key
            BadRequestError: If invalid JSON format in request
            ValidationError: If metadata format is invalid
            NotFoundError: If API key not found
            NetworkError: If connection issues occur

        Note:
            - Only works with live keys
            - Completely replaces existing metadata
            - Sensitive keywords not allowed in metadata
        """
        data = {
            'apiKey': api_key,
            'metadata': metadata
        }
        return self._client._request("POST", f"user/update-api-key-metadata", data=data)

    def update_status(
        self,
        api_key: str,
        status: Literal['active', 'inactive']
    ) -> Dict[str, Any]:
        """
        Update API key status.

        ```bash
        POST /user/api-keys/{api_key}/status
        ```

        Args:
            api_key: The API key to update
            status: New status ('active' or 'inactive')

        Returns:
            Dict containing:

            - message: "API key status updated successfully"
            - api_key: Updated key identifier
            - status: New status value

        Raises:
            AuthenticationError: If authentication fails or missing user ID
            AuthorizationError: If not authorized to modify key
            BadRequestError: If invalid JSON format in request
            ValidationError: If status value is invalid
            NotFoundError: If API key not found
            NetworkError: If connection issues occur

        Note:
            - Deactivated keys will stop working immediately
            - Status change is permanent until changed again
        """
        data = {
            'apiKey': api_key,
            'status': status
        }
        return self._client._request("POST", f"user/api-keys/{api_key}/status", data=data)

    def delete_api_key(self, api_key: str) -> Dict[str, Any]:
        """
        Delete an API key.

        ```bash
        POST /user/delete-api-key
        ```

        Args:
            api_key: The API key to delete

        Returns:
            Dict containing:

            - message: "API key deleted successfully"
            - api_key: Deleted key identifier

        Raises:
            AuthenticationError: If authentication fails or missing user ID
            AuthorizationError: If not authorized to delete key
            BadRequestError: If invalid JSON format in request
            NotFoundError: If API key not found
            NetworkError: If connection issues occur

        Note:
            - Action cannot be undone
            - Key stops working immediately
            - Last live key deletion sets account to inactive
            - Deleted keys remain visible in listings (inactive)
        """
        data = {'apiKey': api_key}
        return self._client._request("POST", "user/delete-api-key", data=data) 