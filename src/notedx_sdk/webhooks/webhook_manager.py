from typing import Dict, Any, Optional, List, TYPE_CHECKING
import logging
import re

from ..exceptions import (
    InvalidFieldError,
    AuthenticationError,
    ValidationError,
)

if TYPE_CHECKING:
    from ..client import NoteDxClient

# Initialize SDK logger
logger = logging.getLogger("notedx_sdk.webhooks")
logger.addHandler(logging.NullHandler())  # Default to no handler
logger.setLevel(logging.INFO)  # Default to INFO level

class WebhookManager:
    """
    Handles webhook configuration and management for the NoteDx API.
    
    This class provides methods for configuring and managing webhook endpoints
    for both development and production environments. Webhooks enable real-time
    notifications for events like note generation completion, errors, and billing updates.
    
    Features:
        - Separate dev/prod webhook URLs
        - HTTPS enforcement for production
        - URL validation and security checks
        - Real-time event notifications
    
    Notes:
        - All methods in this class require Firebase authentication (email/password)
        - API key authentication is not supported for webhook management
    
    Example:
        ```python
        from notedx_sdk import NoteDxClient
        
        # Initialize with email/password
        client = NoteDxClient(
            email="user@example.com",
            password="your-password"
        )
        
        # Get current webhook settings
        settings = client.webhooks.get_webhook_settings()
        print(f"Dev webhook: {settings['webhook_dev']}")
        print(f"Prod webhook: {settings['webhook_prod']}")
        
        # Update webhook URLs
        result = client.webhooks.update_webhook_settings(
            webhook_dev="http://dev.example.com/webhook",
            webhook_prod="https://prod.example.com/webhook"
        )
        ```
    """
    
    # URL validation regex
    _URL_REGEX = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    def __init__(self, client: "NoteDxClient") -> None:
        """
        Initialize the webhook manager.
        
        Args:
            client: The parent NoteDxClient instance
        """
        self._client = client
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.debug("Initialized WebhookManager")

    def _check_firebase_auth(self) -> None:
        """
        Check if Firebase authentication is available.
        
        Raises:
            AuthenticationError: If no Firebase token is available
        """
        if not self._client._token:
            self.logger.error("Firebase authentication required for webhook operations")
            raise AuthenticationError(
                "Firebase authentication (email/password) is required for webhook operations. "
                "API key authentication is not supported."
            )

    def _validate_webhook_url(self, url: str, require_https: bool = False) -> None:
        """
        Validate a webhook URL format and security requirements.
        
        Args:
            url (str): The webhook URL to validate
            require_https (bool): Whether to require HTTPS protocol
            
        Raises:
            ValidationError: If URL format is invalid or security requirements not met
        """
        if not url:  # Allow empty string for removal
            return
            
        if not self._URL_REGEX.match(url):
            raise ValidationError(f"Invalid webhook URL format: {url}")
            
        if require_https and not url.lower().startswith('https://'):
            raise ValidationError(
                f"Production webhook URLs must use HTTPS: {url}"
            )

    def get_webhook_settings(self) -> Dict[str, Any]:
        """
        Retrieve current webhook configuration settings.

        Returns:
            Dict[str, Any]: Current webhook configuration containing:

                - webhook_dev (str): Development webhook URL or None if not set
                - webhook_prod (str): Production webhook URL or None if not set

        Raises:
            AuthenticationError: If Firebase authentication is not available
            AuthorizationError: If not authorized to view webhooks
            NetworkError: If connection issues occur
            NoteDxError: For other API errors

        Example:
            ```python
            # Get current webhook configuration
            settings = client.webhooks.get_webhook_settings()
            
            if settings['webhook_dev']:
                print(f"Dev webhook: {settings['webhook_dev']}")
            else:
                print("No development webhook configured")
                
            if settings['webhook_prod']:
                print(f"Prod webhook: {settings['webhook_prod']}")
            else:
                print("No production webhook configured")
            ```
        """
        self.logger.debug("Retrieving webhook settings")
        
        # Verify Firebase auth
        self._check_firebase_auth()
        
        try:
            response = self._client._request("GET", "user/webhook")
            
            self.logger.info(
                "Successfully retrieved webhook settings",
                extra={
                    'has_dev_webhook': bool(response.get('webhook_dev')),
                    'has_prod_webhook': bool(response.get('webhook_prod'))
                }
            )
            return response
            
        except Exception as e:
            self.logger.error(
                "Failed to retrieve webhook settings",
                extra={'error_type': type(e).__name__},
                exc_info=True
            )
            raise

    def update_webhook_settings(
        self,
        webhook_dev: Optional[str] = None,
        webhook_prod: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update webhook configuration for development and/or production environments.

        Configure URLs where NoteDx will send event notifications. Supports separate
        URLs for development and production environments with different security
        requirements.

        Args:
            webhook_dev (str, optional): Development environment webhook URL.

                - Can use HTTP or HTTPS protocol
                - Set to empty string to remove
                - Must be valid URL format

            webhook_prod (str, optional): Production environment webhook URL.

                - Must use HTTPS protocol
                - Set to empty string to remove
                - Must be valid URL format

        Returns:
            Dict[str, Any]: Update confirmation containing:

                - message (str): "Webhook URLs updated successfully"
                - webhook_dev (str): New dev URL or "unchanged"
                - webhook_prod (str): New prod URL or "unchanged"

        Raises:
            AuthenticationError: If Firebase authentication is not available
            AuthorizationError: If not authorized to update webhooks
            ValidationError: If URLs are invalid or don't meet security requirements
            InvalidFieldError: If no URLs provided to update
            NetworkError: If connection issues occur
            NoteDxError: For other API errors

        Example:
            ```python
            # Update both webhooks
            result = client.webhooks.update_webhook_settings(
                webhook_dev="http://dev.example.com/notedx/webhook",
                webhook_prod="https://api.example.com/notedx/webhook"
            )
            
            # Update only development webhook
            result = client.webhooks.update_webhook_settings(
                webhook_dev="http://localhost:3000/webhook"
            )
            
            # Remove development webhook
            result = client.webhooks.update_webhook_settings(
                webhook_dev=""
            )
            ```
        """
        self.logger.debug(
            "Preparing webhook update",
            extra={
                'updating_dev': webhook_dev is not None,
                'updating_prod': webhook_prod is not None
            }
        )
        
        # Verify Firebase auth
        self._check_firebase_auth()
        
        # Validate input
        if webhook_dev is None and webhook_prod is None:
            self.logger.error("No webhook URLs provided for update")
            raise InvalidFieldError(
                "webhook_urls",
                "At least one webhook URL must be provided"
            )

        # Validate URLs if provided
        try:
            if webhook_dev is not None:
                self._validate_webhook_url(webhook_dev)
                
            if webhook_prod is not None:
                self._validate_webhook_url(webhook_prod, require_https=True)
        except ValidationError as e:
            self.logger.error(
                "Invalid webhook URL format",
                extra={'error': str(e)},
                exc_info=True
            )
            raise

        # Prepare update data
        data = {}
        if webhook_dev is not None:
            data['webhook_dev'] = webhook_dev
        if webhook_prod is not None:
            data['webhook_prod'] = webhook_prod

        try:
            response = self._client._request("POST", "user/webhook", data=data)
            
            self.logger.info(
                "Successfully updated webhook settings",
                extra={
                    'updated_dev': webhook_dev is not None,
                    'updated_prod': webhook_prod is not None,
                    'dev_status': response.get('webhook_dev', 'unchanged'),
                    'prod_status': response.get('webhook_prod', 'unchanged')
                }
            )
            return response
            
        except Exception as e:
            self.logger.error(
                "Failed to update webhook settings",
                extra={'error_type': type(e).__name__},
                exc_info=True
            )
            raise 