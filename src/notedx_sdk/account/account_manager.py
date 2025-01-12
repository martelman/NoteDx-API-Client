from typing import Dict, Any, Optional

from ..exceptions import InvalidFieldError



class AccountManager:
    """
    Handles account management operations for the NoteDx API.
    
    This class provides methods for:
    - Account information retrieval and updates
    - API key management
    - Account lifecycle management
    """
    
    def __init__(self, client):
        """
        Initialize the account manager.
        
        Args:
            client: The parent NoteDxClient instance
        """
        self._client = client

    def get_account(self) -> Dict[str, Any]:
        """
        Get current account information and settings.

        Returns:
            Dict containing:
            - company_name: Company or organization name
            - contact_email: Primary contact email
            - phone_number: Contact phone number
            - address: Business address
            - account_status: Current account status ('active', 'inactive', 'cancelled')
            - created_at: Account creation timestamp (ISO format)

        Raises:
            AuthenticationError: If authentication fails or missing user ID
            AuthorizationError: If not authorized to access this data
            NotFoundError: If user not found
            NetworkError: If connection issues occur

        Note:
            - Requires authentication with email/password
            - Not available with API key authentication
        """
        return self._client._request("GET", "user/account/info")

    def update_account(
        self,
        company_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        phone_number: Optional[str] = None,
        address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update account information and settings.

        Args:
            company_name: New company or organization name
            contact_email: New contact email address
            phone_number: New contact phone number
            address: New business address

        Returns:
            Dict containing:
            - message: "Account information updated successfully"
            - updated_fields: List of fields that were updated

        Raises:
            AuthenticationError: If authentication fails or missing user ID
            AuthorizationError: If not authorized to update account
            BadRequestError: If invalid JSON format in request
            MissingFieldError: If no valid fields provided to update
            ValidationError: If provided values are invalid
            NetworkError: If connection issues occur

        Note:
            - Requires authentication with email/password
            - Not available with API key authentication
            - At least one field must be provided
        """
        update_data = {}
        allowed_fields = ['company_name', 'contact_email', 'phone_number', 'address']
        
        for field, value in {
            'company_name': company_name,
            'contact_email': contact_email,
            'phone_number': phone_number,
            'address': address
        }.items():
            if value is not None:
                update_data[field] = value

        if not update_data:
            raise InvalidFieldError(
                "fields",
                "At least one of these fields must be provided: company_name, contact_email, phone_number, address"
            )

        return self._client._request("POST", "user/account/update", data=update_data)

    def cancel_account(self) -> Dict[str, Any]:
        """
        Cancel the current account.

        This operation:
        1. Deactivates all live API keys
        2. Updates account status to 'cancelled'
        3. Records cancellation timestamp
        4. Triggers final billing process

        Returns:
            Dict containing:
            - message: "Account cancelled successfully"
            - user_id: Account identifier

        Raises:
            AuthenticationError: If authentication fails or missing user ID
            AuthorizationError: If not authorized to cancel
            NotFoundError: If user not found
            PaymentRequiredError: If outstanding balance exists
            NetworkError: If connection issues occur

        Note:
            - Requires email/password authentication
            - All live API keys will be deactivated
            - Final billing will be processed
            - Data retained for 30 days
        """
        return self._client._request("POST", "user/cancel-account")

    def reactivate_account(self) -> Dict[str, Any]:
        """
        Reactivate a cancelled account.

        This operation:
        1. Verifies account is in 'cancelled' state
        2. Checks for unpaid bills
        3. Sets account status to 'inactive'
        4. Records reactivation timestamp

        Returns:
            Dict containing:
            - message: "Account reactivated successfully"
            - user_id: Account identifier

        Raises:
            AuthenticationError: If authentication fails or missing user ID
            AuthorizationError: If not authorized to reactivate
            NotFoundError: If user not found
            BadRequestError: If account is not in cancelled state
            PaymentRequiredError: If unpaid bills exist
            NetworkError: If connection issues occur

        Note:
            - Only cancelled accounts can be reactivated
            - Requires email/password authentication
            - Account will be set to 'inactive' status
            - New API keys must be created after reactivation
            - Previous data remains accessible if within retention period
            - Any unpaid bills must be settled before reactivation
        """
        return self._client._request("POST", "user/reactivate-account") 