from typing import Optional, Dict, Any

class UsageManager:
    """
    Handles usage data operations for the NoteDx API.
    
    This class provides methods for:
    - Retrieving usage statistics
    - Filtering usage by date ranges
    """
    
    def __init__(self, client):
        """
        Initialize the usage manager.
        
        Args:
            client: The parent NoteDxClient instance
        """
        self._client = client

    def get(self, start_month: Optional[str] = None, end_month: Optional[str] = None) -> Dict[str, Any]:
        """
        Get usage data for the authenticated user.

        Args:
            start_month: Optional start month in YYYY-MM format (e.g. "2024-01")
            end_month: Optional end month in YYYY-MM format (e.g. "2024-01")

        Returns:
            Dict containing usage data as per API response

        Raises:
            ValidationError: If date format is invalid
            AuthenticationError: If not authenticated
            PaymentRequiredError: If payment is required
            InactiveAccountError: If account is inactive
            NetworkError: If connection fails
            NoteDxError: For other API errors

        Example:
            >>> # Get all usage data
            >>> usage = client.usage.get()
            >>> 
            >>> # Get usage for specific month
            >>> usage = client.usage.get(start_month="2024-01", end_month="2024-01")
            >>> 
            >>> # Get usage from start month until now
            >>> usage = client.usage.get(start_month="2023-12")
        """
        params = {}
        if start_month:
            params['start_month'] = start_month
        if end_month:
            params['end_month'] = end_month

        return self._client._request("GET", "user/usage", params=params) 