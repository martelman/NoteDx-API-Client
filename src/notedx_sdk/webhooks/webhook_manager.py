from typing import Optional, Dict, Any

from src.notedx_sdk.exceptions import MissingFieldError

class WebhookManager:
    """
    Handles webhook management operations for the NoteDx API.
    
    This class provides methods for:
    - Webhook URL configuration
    - Separate dev/prod webhook management
    """
    
    def __init__(self, client):
        """
        Initialize the webhook manager.
        
        Args:
            client: The parent NoteDxClient instance
        """
        self._client = client

    def get_webhook_settings(self) -> Dict[str, Any]:
        """
        Get current webhook configuration settings.

        Returns:
            Dict containing:
            - webhook_dev: Development webhook URL (or None)
            - webhook_prod: Production webhook URL (or None)

        Raises:
            AuthenticationError: If authentication fails or missing user ID
            AuthorizationError: If not authorized to view webhooks
            NetworkError: If connection issues occur

        Note:
            - Requires authentication with email/password
            - Returns None for unconfigured webhooks
        """
        return self._client._request("GET", "user/webhooks")

    def update_webhook_settings(
        self,
        webhook_dev: Optional[str] = None,
        webhook_prod: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update webhook configuration settings.

        Updates webhook URLs for development and/or production environments.
        At least one URL must be provided.

        Args:
            webhook_dev: Development environment webhook URL
                       Can be HTTP or HTTPS
                       Set to empty string to remove
            webhook_prod: Production environment webhook URL
                        Must be HTTPS
                        Set to empty string to remove

        Returns:
            Dict containing:
            - message: "Webhook URLs updated successfully"
            - webhook_dev: New dev URL or "unchanged"
            - webhook_prod: New prod URL or "unchanged"

        Raises:
            AuthenticationError: If authentication fails or missing user ID
            AuthorizationError: If not authorized to update webhooks
            BadRequestError: If invalid JSON format in request
            ValidationError: If URLs are invalid
            MissingFieldError: If no URLs provided
            NetworkError: If connection issues occur

        Note:
            - Production URLs must use HTTPS
            - Development URLs can use HTTP or HTTPS
            - Empty string clears the URL
            - At least one URL must be provided
        """
        if webhook_dev is None and webhook_prod is None:
            raise MissingFieldError("At least one webhook URL (webhook_dev or webhook_prod) must be provided")

        data = {}
        if webhook_dev is not None:
            data['webhookDev'] = webhook_dev
        if webhook_prod is not None:
            data['webhookProd'] = webhook_prod

        return self._client._request("POST", "user/webhook", data=data) 