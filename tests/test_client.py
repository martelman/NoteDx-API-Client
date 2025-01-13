import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from src.notedx_sdk import NoteDxClient
from src.notedx_sdk.exceptions import (
    NoteDxError,
    AuthenticationError,
    AuthorizationError,
    PaymentRequiredError,
    InactiveAccountError,
    NotFoundError,
    BadRequestError,
    RateLimitError,
    NetworkError,
    InternalServerError,
)

# Test initialization and configuration
class TestClientInitialization:
    def test_init_with_api_key(self):
        """Test client initialization with API key"""
        client = NoteDxClient(api_key="test-key", auto_login=False)
        assert client._api_key == "test-key"
        assert client._email is None
        assert client._password is None

    @patch('requests.Session.request')
    def test_init_with_email_password(self, mock_request):
        """Test client initialization with email/password"""
        client = NoteDxClient(email="test@example.com", password="test-pass", auto_login=False)
        assert client._email == "test@example.com"
        assert client._password == "test-pass"
        assert client._api_key is None

    def test_init_no_credentials(self):
        """Test client initialization with no credentials raises error"""
        with pytest.raises(AuthenticationError) as exc_info:
            NoteDxClient()
        assert "No authentication credentials provided" in str(exc_info.value)

    @patch.dict('os.environ', {'NOTEDX_API_KEY': 'env-api-key'})
    def test_init_from_env_vars(self):
        """Test client initialization from environment variables"""
        client = NoteDxClient(auto_login=False)
        assert client._api_key == "env-api-key"

    def test_configure_logging(self):
        """Test logging configuration"""
        import logging
        handler = logging.StreamHandler()
        NoteDxClient.configure_logging(level=logging.DEBUG, handler=handler)
        logger = logging.getLogger("notedx_sdk")
        assert logger.level == logging.DEBUG
        assert handler in logger.handlers

# Test authentication methods
class TestAuthentication:
    @patch('requests.Session.request')
    def test_login_success(self, mock_request):
        """Test successful login with email/password"""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user_id": "test-user",
            "id_token": "test-token",
            "refresh_token": "test-refresh",
            "email": "test@example.com"
        }
        mock_request.return_value = mock_response

        # Create client and login
        client = NoteDxClient(email="test@example.com", password="test-pass", auto_login=False)
        result = client.login()

        # Verify request
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs['json'] == {
            "email": "test@example.com",
            "password": "test-pass"
        }
        assert client._token == "test-token"
        assert client._refresh_token == "test-refresh"
        assert client._user_id == "test-user"

    @patch('requests.Session.request')
    def test_login_invalid_credentials(self, mock_request):
        """Test login with invalid credentials"""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {
                "code": "UNAUTHORIZED",
                "message": "Invalid credentials"
            }
        }
        mock_request.return_value = mock_response

        client = NoteDxClient(email="test@example.com", password="wrong-pass", auto_login=False)
        with pytest.raises(AuthenticationError) as exc_info:
            client.login()
        assert "Invalid credentials" in str(exc_info.value)

    @patch('requests.Session.request')
    def test_refresh_token_success(self, mock_request):
        """Test successful token refresh"""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id_token": "new-token",
            "refresh_token": "new-refresh",
            "user_id": "test-user"
        }
        mock_request.return_value = mock_response

        client = NoteDxClient(api_key="test-key", auto_login=False)
        client._refresh_token = "old-refresh-token"
        result = client.refresh_token()

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs['json'] == {"refresh_token": "old-refresh-token"}
        assert client._token == "new-token"
        assert client._refresh_token == "new-refresh"

    def test_refresh_token_no_token(self):
        """Test token refresh with no refresh token"""
        client = NoteDxClient(api_key="test-key", auto_login=False)
        client._refresh_token = None
        
        with pytest.raises(AuthenticationError) as exc_info:
            client.refresh_token()
        assert "No refresh token available" in str(exc_info.value)

# Test request handling
class TestRequestHandling:
    @patch('requests.Session.request')
    def test_request_with_api_key(self, mock_request):
        """Test request with API key authentication"""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response

        client = NoteDxClient(api_key="test-api-key", auto_login=False)
        result = client._request("GET", "test/endpoint")

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs['headers']['X-Api-Key'] == "test-api-key"
        assert result == {"data": "test"}

    @patch('requests.Session.request')
    def test_request_with_token(self, mock_request):
        """Test request with token authentication"""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response

        client = NoteDxClient(api_key="test-api-key", auto_login=False)
        client._token = "test-token"
        result = client._request("GET", "test/endpoint")

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs['headers']['Authorization'] == "Bearer test-token"
        assert result == {"data": "test"}

    @patch('requests.Session.request')
    def test_request_retry_on_401(self, mock_request):
        """Test request retry on 401 error"""
        # Setup mock responses
        mock_error = Mock()
        mock_error.status_code = 401
        mock_error.json.return_value = {
            "error": {
                "code": "TOKEN_EXPIRED",
                "message": "Token expired"
            }
        }

        mock_success = Mock()
        mock_success.status_code = 200
        mock_success.json.return_value = {"data": "success"}

        mock_request.side_effect = [mock_error, mock_success]

        client = NoteDxClient(api_key="test-api-key", auto_login=False)
        client._token = "expired-token"
        client._refresh_token = "refresh-token"

        with patch.object(client, 'refresh_token') as mock_refresh:
            mock_refresh.return_value = {"id_token": "new-token"}
            result = client._request("GET", "test/endpoint")

        assert mock_request.call_count == 2
        assert result == {"data": "success"}

    @patch('requests.Session.request')
    def test_request_rate_limit(self, mock_request):
        """Test handling of rate limit responses"""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'X-RateLimit-Reset': '1234567890'}
        mock_response.json.return_value = {"message": "Rate limit exceeded"}
        mock_request.return_value = mock_response

        client = NoteDxClient(api_key="test-api-key", auto_login=False)
        with pytest.raises(RateLimitError) as exc_info:
            client._request("GET", "test/endpoint")
        assert "API rate limit exceeded" in str(exc_info.value)

    @patch('requests.Session.request')
    def test_request_network_error(self, mock_request):
        """Test handling of network errors"""
        mock_request.side_effect = requests.ConnectionError("Connection failed")

        client = NoteDxClient(api_key="test-api-key", auto_login=False)
        with pytest.raises(NetworkError) as exc_info:
            client._request("GET", "test/endpoint")
        assert "Connection error" in str(exc_info.value)

    @patch('requests.Session.request')
    def test_request_timeout(self, mock_request):
        """Test handling of request timeouts"""
        mock_request.side_effect = requests.Timeout("Request timed out")

        client = NoteDxClient(api_key="test-api-key", auto_login=False)
        with pytest.raises(NetworkError) as exc_info:
            client._request("GET", "test/endpoint")
        assert "Request timed out" in str(exc_info.value)

# Test error handling
class TestErrorHandling:
    @pytest.mark.parametrize("status_code,exception_class,error_msg", [
        (400, BadRequestError, "Bad request"),
        (401, AuthenticationError, "Invalid credentials"),
        (402, PaymentRequiredError, "Payment required"),
        (403, AuthorizationError, "Not authorized"),
        (404, NotFoundError, "Resource not found"),
        (500, InternalServerError, "Server error"),
    ])
    @patch('requests.Session.request')
    def test_error_responses(self, mock_request, status_code, exception_class, error_msg):
        """Test handling of various error responses"""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = {
            "message": error_msg,
            "error": {"code": "ERROR_CODE"}
        }
        mock_request.return_value = mock_response

        client = NoteDxClient(api_key="test-api-key", auto_login=False)
        with pytest.raises(exception_class) as exc_info:
            client._request("GET", "test/endpoint")
        assert error_msg in str(exc_info.value)

# Test utility methods
class TestUtilityMethods:
    def test_redact_sensitive_data(self):
        """Test redaction of sensitive information"""
        client = NoteDxClient(api_key="test-api-key", auto_login=False)
        test_data = {
            "email": "test@example.com",
            "password": "secret",
            "api_key": "test-key",
            "token": "bearer-token",
            "public": "visible",
            "nested": {
                "secret": "hidden",
                "visible": "shown"
            }
        }

        redacted = client._redact_sensitive_data(test_data)

        assert redacted["email"] == "test@example.com"
        assert redacted["password"] == "***"
        assert redacted["api_key"] == "***"
        assert redacted["token"] == "***"
        assert redacted["public"] == "visible"
        assert redacted["nested"]["secret"] == "***"
        assert redacted["nested"]["visible"] == "shown"

    def test_set_token(self):
        """Test manual token setting"""
        client = NoteDxClient(api_key="test-api-key", auto_login=False)
        client.set_token("test-token", "test-refresh")
        assert client._token == "test-token"
        assert client._refresh_token == "test-refresh"

    def test_set_api_key(self):
        """Test manual API key setting"""
        client = NoteDxClient(api_key="test-api-key", auto_login=False)
        client.set_api_key("new-api-key")
        assert client._api_key == "new-api-key"
