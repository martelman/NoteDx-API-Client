import pytest
from unittest.mock import patch

from notedx_sdk.exceptions import (
    AuthenticationError,
    AuthorizationError,
    InvalidFieldError,
    MissingFieldError,
    InactiveAccountError
)

@pytest.mark.unit
class TestAccountManager:
    @patch('requests.request')
    def test_get_account_success(self, mock_request, mock_client):
        mock_client._request.return_value = {
            "id": "test-id",
            "email": "test@example.com",
            "company_name": "Test Company",
            "phone_number": "+1234567890",
            "contact_email": "contact@example.com",
            "created_at": "2024-01-01T00:00:00Z",
            "status": "active"
        }

        response = mock_client.account.get_account()
        assert response["id"] == "test-id"
        assert response["email"] == "test@example.com"
        assert response["company_name"] == "Test Company"
        assert response["status"] == "active"

    @patch('requests.request')
    def test_get_account_unauthorized(self, mock_request, mock_client):
        mock_client._request.side_effect = AuthenticationError("Missing Authentication Token")
        with pytest.raises(AuthenticationError):
            mock_client.account.get_account()

    @patch('requests.request')
    def test_update_account_success(self, mock_request, mock_client):
        update_data = {
            "company_name": "Updated Company",
            "phone_number": "+9876543210",
            "contact_email": "new@example.com"
        }
        mock_client._request.return_value = {
            "message": "Account updated successfully",
            "status": "success"
        }

        response = mock_client.account.update_account(**update_data)
        assert response["message"] == "Account updated successfully"
        assert response["status"] == "success"

    @patch('requests.request')
    def test_account_inactive(self, mock_request, mock_client):
        mock_client._request.side_effect = InactiveAccountError("Account is inactive")
        with pytest.raises(InactiveAccountError):
            mock_client.account.get_account()

    @patch('requests.request')
    def test_cancel_account_success(self, mock_request, mock_client):
        mock_client._request.return_value = {
            "message": "Account cancelled successfully",
            "status": "success"
        }

        response = mock_client.account.cancel_account()
        assert response["message"] == "Account cancelled successfully"
        assert response["status"] == "success"

    @patch('requests.request')
    def test_reactivate_account_success(self, mock_request, mock_client):
        mock_client._request.return_value = {
            "message": "Account reactivated successfully",
            "status": "success"
        }

        response = mock_client.account.reactivate_account()
        assert response["message"] == "Account reactivated successfully"
        assert response["status"] == "success"

    @patch('requests.request')
    def test_reactivate_account_not_cancelled(self, mock_request, mock_client):
        mock_client._request.side_effect = AuthorizationError("Account is not cancelled")
        with pytest.raises(AuthorizationError):
            mock_client.account.reactivate_account() 