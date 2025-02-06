import pytest
from unittest.mock import Mock, patch
from src.notedx_sdk.account.account_manager import AccountManager
from src.notedx_sdk.exceptions import (
    AuthenticationError,
    InvalidFieldError,
    NetworkError,
    MissingFieldError,
    BadRequestError,
)

@pytest.fixture
def mock_client():
    """Create a mock NoteDxClient with a valid Firebase token."""
    client = Mock()
    client._token = "mock-firebase-token"
    return client

@pytest.fixture
def account_manager(mock_client):
    """Create an AccountManager instance with a mock client."""
    return AccountManager(mock_client)

class TestAccountManager:
    def test_init(self, account_manager):
        """Test AccountManager initialization."""
        assert account_manager._client is not None
        assert account_manager.logger is not None

    def test_check_firebase_auth_with_token(self, account_manager):
        """Test _check_firebase_auth when token is present."""
        # Should not raise any exception
        account_manager._check_firebase_auth()

    def test_check_firebase_auth_without_token(self, mock_client):
        """Test _check_firebase_auth when token is missing."""
        mock_client._token = None
        manager = AccountManager(mock_client)
        
        with pytest.raises(AuthenticationError) as exc_info:
            manager._check_firebase_auth()
        assert "Firebase authentication" in str(exc_info.value)

    def test_get_account_success(self, account_manager):
        """Test successful account information retrieval."""
        expected_response = {
            "company_name": "Test Corp",
            "contact_email": "test@example.com",
            "phone_number": "+1234567890",
            "address": "123 Test St",
            "account_status": "active",
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        account_manager._client._request.return_value = expected_response
        
        result = account_manager.get_account()
        
        account_manager._client._request.assert_called_once_with(
            "GET", "user/account/info"
        )
        assert result == expected_response

    def test_get_account_network_error(self, account_manager):
        """Test account retrieval with network error."""
        account_manager._client._request.side_effect = NetworkError("Connection failed")
        
        with pytest.raises(NetworkError) as exc_info:
            account_manager.get_account()
        assert "Connection failed" in str(exc_info.value)

    @pytest.mark.parametrize(
        "update_data,expected_payload",
        [
            (
                {
                    "company_name": "New Corp",
                    "contact_email": "new@example.com"
                },
                {
                    "company_name": "New Corp",
                    "contact_email": "new@example.com"
                }
            ),
            (
                {
                    "phone_number": "+1987654321",
                    "address": "123 Main St"
                },
                {
                    "phone_number": "+1987654321",
                    "address": "123 Main St"
                }
            )
        ]
    )
    def test_update_account_success(self, account_manager, update_data, expected_payload):
        """Test successful account updates with different field combinations."""
        expected_response = {
            "message": "Account information updated successfully",
            "updated_fields": list(update_data.keys())
        }
        account_manager._client._request.return_value = expected_response
        
        result = account_manager.update_account(**update_data)
        
        account_manager._client._request.assert_called_once_with(
            "POST",
            "user/account/update",
            data=expected_payload
        )
        assert result == expected_response

    def test_cancel_account_success(self, account_manager):
        """Test successful account cancellation."""
        expected_response = {
            "message": "Account cancelled successfully",
            "user_id": "test-user-123"
        }
        account_manager._client._request.return_value = expected_response
        
        result = account_manager.cancel_account()
        
        account_manager._client._request.assert_called_once_with(
            "POST", "user/cancel-account"
        )
        assert result == expected_response

    def test_reactivate_account_success(self, account_manager):
        """Test successful account reactivation."""
        expected_response = {
            "message": "Account reactivated successfully",
            "user_id": "test-user-123"
        }
        account_manager._client._request.return_value = expected_response
        
        result = account_manager.reactivate_account()
        
        account_manager._client._request.assert_called_once_with(
            "POST", "user/reactivate-account"
        )
        assert result == expected_response

    @pytest.mark.parametrize(
        "method_name,endpoint",
        [
            ("get_account", "user/account/info"),
            ("cancel_account", "user/cancel-account"),
            ("reactivate_account", "user/reactivate-account")
        ]
    )
    def test_methods_require_authentication(self, mock_client, method_name, endpoint):
        """Test that all account methods require authentication."""
        mock_client._token = None
        manager = AccountManager(mock_client)
        
        method = getattr(manager, method_name)
        with pytest.raises(AuthenticationError) as exc_info:
            method()
        assert "Firebase authentication" in str(exc_info.value)
        mock_client._request.assert_not_called()
