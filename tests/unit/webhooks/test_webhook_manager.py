import pytest
from unittest.mock import Mock, patch
from src.notedx_sdk.webhooks.webhook_manager import WebhookManager
from src.notedx_sdk.exceptions import (
    ValidationError,
    AuthenticationError,
    InvalidFieldError,
)

@pytest.fixture
def mock_client():
    """Create a mock NoteDxClient."""
    client = Mock()
    client._token = "mock-firebase-token"
    return client

@pytest.fixture
def webhook_manager(mock_client):
    """Create a WebhookManager instance with a mock client."""
    return WebhookManager(mock_client)

@pytest.fixture
def mock_webhook_settings():
    """Sample response for webhook settings."""
    return {
        "webhook_dev": "http://dev.example.com/webhook",
        "webhook_prod": "https://prod.example.com/webhook"
    }

class TestWebhookManager:
    def test_init(self, webhook_manager):
        """Test WebhookManager initialization."""
        assert webhook_manager._client is not None
        assert webhook_manager.logger is not None

    def test_check_firebase_auth_with_token(self, webhook_manager):
        """Test _check_firebase_auth when token is present."""
        webhook_manager._check_firebase_auth()  # Should not raise any exception

    def test_check_firebase_auth_without_token(self, mock_client):
        """Test _check_firebase_auth when token is missing."""
        mock_client._token = None
        manager = WebhookManager(mock_client)
        
        with pytest.raises(AuthenticationError) as exc_info:
            manager._check_firebase_auth()
        assert "Firebase authentication" in str(exc_info.value)
        assert "API key authentication is not supported" in str(exc_info.value)

    @pytest.mark.parametrize(
        "url,require_https,should_raise,error_message",
        [
            ("https://example.com/webhook", True, False, None),
            ("https://example.com/webhook", False, False, None),
            ("http://localhost:3000/webhook", False, False, None),
            ("http://dev.example.com/webhook", False, False, None),
            ("http://prod.example.com/webhook", True, True, "must use HTTPS"),
            ("not-a-url", False, True, "Invalid webhook URL format"),
            ("ftp://example.com", False, True, "Invalid webhook URL format"),
            ("", False, False, None),  # Empty string is allowed for removal
            ("http://example.com/webhook?token=123&type=note", False, False, None),
            ("https://sub1.sub2.example.com/webhook/path", True, False, None),
        ]
    )
    def test_validate_webhook_url(self, webhook_manager, url, require_https, should_raise, error_message):
        """Test webhook URL validation with various inputs."""
        if should_raise:
            with pytest.raises(ValidationError) as exc_info:
                webhook_manager._validate_webhook_url(url, require_https)
            assert error_message in str(exc_info.value)
        else:
            webhook_manager._validate_webhook_url(url, require_https)

    def test_get_webhook_settings_success(self, webhook_manager, mock_webhook_settings):
        """Test successful retrieval of webhook settings."""
        webhook_manager._client._request.return_value = mock_webhook_settings

        result = webhook_manager.get_webhook_settings()

        webhook_manager._client._request.assert_called_once_with(
            "GET", "user/webhook"
        )
        assert result == mock_webhook_settings
        assert "webhook_dev" in result
        assert "webhook_prod" in result

    def test_get_webhook_settings_network_error(self, webhook_manager):
        """Test handling of network errors when getting webhook settings."""
        webhook_manager._client._request.side_effect = Exception("Connection failed")

        with pytest.raises(Exception) as exc_info:
            webhook_manager.get_webhook_settings()
        assert "Connection failed" in str(exc_info.value)

    @pytest.mark.parametrize(
        "webhook_dev,webhook_prod,expected_data",
        [
            (
                "http://dev.example.com/webhook",
                "https://prod.example.com/webhook",
                {
                    "webhook_dev": "http://dev.example.com/webhook",
                    "webhook_prod": "https://prod.example.com/webhook"
                }
            ),
            (
                "http://localhost:3000/webhook",
                None,
                {
                    "webhook_dev": "http://localhost:3000/webhook"
                }
            ),
            (
                None,
                "https://api.example.com/webhook",
                {
                    "webhook_prod": "https://api.example.com/webhook"
                }
            ),
            (
                "",
                None,
                {
                    "webhook_dev": ""
                }
            ),
        ]
    )
    def test_update_webhook_settings_success(self, webhook_manager, webhook_dev, webhook_prod, expected_data):
        """Test successful webhook settings updates with different combinations."""
        expected_response = {
            "message": "Webhook URLs updated successfully",
            "webhook_dev": webhook_dev if webhook_dev is not None else "unchanged",
            "webhook_prod": webhook_prod if webhook_prod is not None else "unchanged"
        }
        webhook_manager._client._request.return_value = expected_response

        result = webhook_manager.update_webhook_settings(
            webhook_dev=webhook_dev,
            webhook_prod=webhook_prod
        )

        webhook_manager._client._request.assert_called_once_with(
            "POST",
            "user/webhook",
            data=expected_data
        )
        assert result == expected_response

    def test_update_webhook_settings_no_urls(self, webhook_manager):
        """Test update with no webhook URLs provided."""
        with pytest.raises(InvalidFieldError) as exc_info:
            webhook_manager.update_webhook_settings()
        assert "At least one webhook URL must be provided" in str(exc_info.value)

    def test_update_webhook_settings_invalid_prod_url(self, webhook_manager):
        """Test update with invalid production webhook URL (non-HTTPS)."""
        with pytest.raises(ValidationError) as exc_info:
            webhook_manager.update_webhook_settings(
                webhook_prod="http://example.com/webhook"  # Should be HTTPS
            )
        assert "must use HTTPS" in str(exc_info.value)

    def test_update_webhook_settings_network_error(self, webhook_manager):
        """Test handling of network errors when updating webhook settings."""
        webhook_manager._client._request.side_effect = Exception("Connection failed")

        with pytest.raises(Exception) as exc_info:
            webhook_manager.update_webhook_settings(webhook_dev="http://dev.example.com/webhook")
        assert "Connection failed" in str(exc_info.value)
