from typing import Dict, Any, Optional, TYPE_CHECKING
import logging

from ..exceptions import (
    InvalidFieldError,
    AuthenticationError,
)

if TYPE_CHECKING:
    from ..client import NoteDxClient

# Initialize SDK logger
logger = logging.getLogger("notedx_sdk.account")
logger.addHandler(logging.NullHandler())  # Default to no handler
logger.setLevel(logging.INFO)  # Default to INFO level

class AccountManager:
    """
    Handles account management operations for the NoteDx API.
    
    This class provides methods for:

    - Account information retrieval and updates
    - Account lifecycle management
    
    Note:
        All methods in this class require Firebase authentication (email/password).
        API key authentication is not supported for account management operations.
    
    Example:
        ```python
        from notedx_sdk import NoteDxClient
        
        # Initialize with email/password
        client = NoteDxClient(
            email="user@example.com",
            password="your-password"
        )
        
        # Get account info
        account_info = client.account.get_account()
        print(f"Company: {account_info['company_name']}")
        
        # Update account
        result = client.account.update_account(
            company_name="New Company Name",
            contact_email="new@email.com"
        )
        ```
    """
    
    def __init__(self, client: "NoteDxClient") -> None:
        """
        Initialize the account manager.
        
        Args:
            client: The parent NoteDxClient instance
        """
        self._client = client
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.debug("Initialized AccountManager")

    def _check_firebase_auth(self) -> None:
        """
        Check if Firebase authentication is available.
        
        Raises:
            AuthenticationError: If no Firebase token is available
        """
        if not self._client._token:
            self.logger.error("Firebase authentication required for account operations")
            raise AuthenticationError(
                "Firebase authentication (email/password) is required for account operations. "
                "API key authentication is not supported."
            )

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
            AuthenticationError: If Firebase authentication is not available
            AuthorizationError: If not authorized to access this data
            NotFoundError: If user not found
            NetworkError: If connection issues occur

        Example:
            ```python
            account_info = client.account.get_account()
            print(f"Account Status: {account_info['account_status']}")
            ```
        """
        self.logger.debug("Initiating account information retrieval")
        
        # Verify Firebase auth
        self._check_firebase_auth()
        
        try:
            response = self._client._request("GET", "user/account/info")
            
            # Log success with redacted info
            log_data = {
                'status': response.get('account_status'),
                'company': response.get('company_name')
            }
            self.logger.info("Successfully retrieved account information", extra=log_data)
            return response
            
        except Exception as e:
            self.logger.error(
                "Failed to retrieve account information",
                extra={'error_type': type(e).__name__},
                exc_info=True
            )
            raise

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
            AuthenticationError: If Firebase authentication is not available
            AuthorizationError: If not authorized to update account
            BadRequestError: If invalid JSON format in request
            InvalidFieldError: If no valid fields provided to update
            NetworkError: If connection issues occur

        Example:
            ```python
            result = client.account.update_account(
                company_name="New Corp",
                contact_email="contact@newcorp.com"
            )
            print(f"Updated fields: {result['updated_fields']}")
            ```
        """
        self.logger.debug("Preparing account update")
        
        # Verify Firebase auth
        self._check_firebase_auth()
        
        # Prepare update data
        update_data = {}
        allowed_fields = ['company_name', 'contact_email', 'phone_number', 'address']
        
        # Log provided fields (without values)
        self.logger.debug(
            "Fields provided for update",
            extra={
                'fields': {
                    'company_name': company_name is not None,
                    'contact_email': contact_email is not None,
                    'phone_number': phone_number is not None,
                    'address': address is not None
                }
            }
        )
        
        for field, value in {
            'company_name': company_name,
            'contact_email': contact_email,
            'phone_number': phone_number,
            'address': address
        }.items():
            if value is not None:
                update_data[field] = value

        if not update_data:
            self.logger.warning(
                "No valid fields provided for update",
                extra={'allowed_fields': allowed_fields}
            )
            raise InvalidFieldError(
                "fields",
                "At least one of these fields must be provided: company_name, contact_email, phone_number, address"
            )

        try:
            response = self._client._request(
                "POST",
                "user/account/update",
                data=update_data
            )
            
            self.logger.info(
                "Successfully updated account information",
                extra={'updated_fields': list(update_data.keys())}
            )
            return response
            
        except Exception as e:
            self.logger.error(
                "Failed to update account information",
                extra={
                    'error_type': type(e).__name__,
                    'attempted_fields': list(update_data.keys())
                },
                exc_info=True
            )
            raise

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
            AuthenticationError: If Firebase authentication is not available
            AuthorizationError: If not authorized to cancel
            NotFoundError: If user not found
            PaymentRequiredError: If outstanding balance exists
            NetworkError: If connection issues occur

        Example:
            ```python
            result = client.account.cancel_account()
            print(f"Account {result['user_id']} cancelled")
            ```
        """
        self.logger.debug("Initiating account cancellation")
        
        # Verify Firebase auth
        self._check_firebase_auth()
        
        try:
            response = self._client._request("POST", "user/cancel-account")
            
            self.logger.info(
                "Successfully cancelled account",
                extra={'user_id': response.get('user_id')}
            )
            return response
            
        except Exception as e:
            self.logger.error(
                "Failed to cancel account",
                extra={'error_type': type(e).__name__},
                exc_info=True
            )
            raise

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
            AuthenticationError: If Firebase authentication is not available
            AuthorizationError: If not authorized to reactivate
            NotFoundError: If user not found
            BadRequestError: If account is not in cancelled state
            PaymentRequiredError: If unpaid bills exist
            NetworkError: If connection issues occur

        Example:
            ```python
            result = client.account.reactivate_account()
            print(f"Account {result['user_id']} reactivated")
            ```

        Note:
            - Only cancelled accounts can be reactivated
            - Account will be set to 'inactive' status
            - New API keys must be created after reactivation
            - Previous data remains accessible if within retention period
        """
        self.logger.debug("Initiating account reactivation")
        
        # Verify Firebase auth
        self._check_firebase_auth()
        
        try:
            response = self._client._request("POST", "user/reactivate-account")
            
            self.logger.info(
                "Successfully reactivated account",
                extra={'user_id': response.get('user_id')}
            )
            return response
            
        except Exception as e:
            self.logger.error(
                "Failed to reactivate account",
                extra={'error_type': type(e).__name__},
                exc_info=True
            )
            raise 