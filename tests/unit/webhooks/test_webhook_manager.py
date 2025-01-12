import pytest
from unittest.mock import patch

from notedx_sdk.exceptions import (
    AuthenticationError,
    ValidationError,
    InactiveAccountError,
    MissingFieldError,
    InvalidFieldError
)

@pytest.mark.unit
class TestWebhookManager:
    @patch('requests.request')
    def test_get_webhook_settings_success(self, mock_request, mock_client):
        mock_client._request.return_value = {
            "webhook_dev": "https://dev.example.com/webhook",
            "webhook_prod": "https://prod.example.com/webhook"
        }

        response = mock_client.webhooks.get_webhook_settings()
        assert response["webhook_dev"] == "https://dev.example.com/webhook"
        assert response["webhook_prod"] == "https://prod.example.com/webhook"

    @patch('requests.request')
    def test_update_webhook_settings_success(self, mock_request, mock_client):
        mock_client._request.return_value = {
            "message": "Webhook settings updated successfully",
            "status": "success",
            "webhook_dev": "https://dev.example.com/webhook",
            "webhook_prod": "https://prod.example.com/webhook"
        }

        response = mock_client.webhooks.update_webhook_settings(
            webhook_dev="https://dev.example.com/webhook",
            webhook_prod="https://prod.example.com/webhook"
        )
        assert response["message"] == "Webhook settings updated successfully"
        assert response["webhook_dev"] == "https://dev.example.com/webhook"
        assert response["webhook_prod"] == "https://prod.example.com/webhook"

    @patch('requests.request')
    def test_update_webhook_settings_invalid_dev_url(self, mock_request, mock_client):
        mock_client._request.side_effect = ValidationError("Invalid development webhook URL")
        with pytest.raises(ValidationError):
            mock_client.webhooks.update_webhook_settings(
                webhook_dev="invalid-url",
                webhook_prod="https://prod.example.com/webhook"
            )

    @patch('requests.request')
    def test_update_webhook_settings_invalid_prod_url(self, mock_request, mock_client):
        mock_client._request.side_effect = ValidationError("Invalid production webhook URL")
        with pytest.raises(ValidationError):
            mock_client.webhooks.update_webhook_settings(
                webhook_dev="https://dev.example.com/webhook",
                webhook_prod="invalid-url"
            )

    @patch('requests.request')
    def test_webhook_settings_unauthorized(self, mock_request, mock_client):
        mock_client._request.side_effect = AuthenticationError("Missing Authentication Token")
        with pytest.raises(AuthenticationError):
            mock_client.webhooks.get_webhook_settings()

    @patch('requests.request')
    def test_webhook_settings_inactive_account(self, mock_request, mock_client):
        mock_client._request.side_effect = InactiveAccountError("Account is inactive")
        with pytest.raises(InactiveAccountError):
            mock_client.webhooks.get_webhook_settings() 