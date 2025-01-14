import os
import pytest
import requests
from src.notedx_sdk.helpers import get_env, parse_response, build_headers
from src.notedx_sdk.exceptions import (
    NoteDxError,
    AuthenticationError,
    BadRequestError,
    PaymentRequiredError,
    InactiveAccountError,
    NotFoundError,
    InternalServerError
)

class TestGetEnv:
    def test_get_existing_env(self, monkeypatch):
        """Test getting an existing environment variable"""
        expected_value = "test_value"
        monkeypatch.setenv("TEST_KEY", expected_value)
        assert get_env("TEST_KEY") == expected_value

    def test_get_non_existing_env_with_default(self):
        """Test getting a non-existing environment variable with default value"""
        default_value = "default"
        assert get_env("NON_EXISTING_KEY", default_value) == default_value

    def test_get_non_existing_env_without_default(self):
        """Test getting a non-existing environment variable without default value"""
        assert get_env("NON_EXISTING_KEY") == ""

class TestParseResponse:
    def test_successful_json_response(self):
        """Test parsing a successful JSON response"""
        mock_response = requests.Response()
        mock_response.status_code = 200
        mock_response._content = b'{"key": "value"}'
        result = parse_response(mock_response)
        assert result == {"key": "value"}

    def test_successful_non_json_response(self):
        """Test parsing a successful non-JSON response"""
        mock_response = requests.Response()
        mock_response.status_code = 200
        mock_response._content = b'Not JSON'
        result = parse_response(mock_response)
        assert result == {"detail": "Not JSON"}

    @pytest.mark.parametrize("status_code,exception_class,content", [
        (400, BadRequestError, b'{"message": "Bad request"}'),
        (401, AuthenticationError, b'{"detail": "Unauthorized"}'),
        (402, PaymentRequiredError, b'{"message": "Payment required"}'),
        (403, InactiveAccountError, b'{"detail": "Forbidden"}'),
        (404, NotFoundError, b'{"message": "Not found"}'),
        (500, InternalServerError, b'{"detail": "Server error"}'),
        (418, NoteDxError, b'{"message": "I\'m a teapot"}'),
    ])
    def test_error_responses(self, status_code, exception_class, content):
        """Test parsing various error responses"""
        mock_response = requests.Response()
        mock_response.status_code = status_code
        mock_response._content = content
        
        with pytest.raises(exception_class):
            parse_response(mock_response)

    def test_error_response_with_plain_text(self):
        """Test parsing error response with plain text instead of JSON"""
        mock_response = requests.Response()
        mock_response.status_code = 500
        mock_response._content = b'Internal Server Error'
        
        with pytest.raises(InternalServerError) as exc_info:
            parse_response(mock_response)
        assert str(exc_info.value) == "Internal Server Error"

class TestBuildHeaders:
    def test_headers_with_token(self):
        """Test building headers with Firebase token"""
        token = "test_token"
        headers = build_headers(token=token)
        assert headers == {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

    def test_headers_with_api_key(self):
        """Test building headers with API key"""
        api_key = "test_api_key"
        headers = build_headers(api_key=api_key)
        assert headers == {
            "Content-Type": "application/json",
            "X-Api-Key": api_key
        }

    def test_headers_with_both_credentials(self):
        """Test building headers with both token and API key (token should take precedence)"""
        token = "test_token"
        api_key = "test_api_key"
        headers = build_headers(token=token, api_key=api_key)
        assert headers == {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

    def test_headers_without_credentials(self):
        """Test building headers without any credentials"""
        headers = build_headers()
        assert headers == {"Content-Type": "application/json"} 