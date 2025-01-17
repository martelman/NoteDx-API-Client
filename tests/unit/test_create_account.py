import pytest
from unittest.mock import patch
from src.notedx_sdk.client import NoteDxClient
from src.notedx_sdk.exceptions import (

    NetworkError
)

class TestCreateAccount:
    def test_create_account_success(self):
        """Test successful account creation."""
        pass

    def test_create_account_email_exists(self):
        """Test account creation with existing email."""
        pass

    def test_create_account_network_error(self):
        """Test account creation with network error."""
        with patch.object(NoteDxClient, '_create_account_request') as mock_request:
            mock_request.side_effect = NetworkError("Connection failed")

            with pytest.raises(NetworkError) as exc_info:
                NoteDxClient.create_account(
                    email="test@example.com",
                    password="test-password",
                    company_name="Test Corp"
                )
            assert "Connection failed" in str(exc_info.value)

    def test_create_account_missing_required_fields(self):
        """Test account creation with missing required fields."""
        with pytest.raises(TypeError) as exc_info:
            NoteDxClient.create_account(
                email="test@example.com",
                password="test-password"
            )
        assert "missing 1 required positional argument: 'company_name'" in str(exc_info.value) 