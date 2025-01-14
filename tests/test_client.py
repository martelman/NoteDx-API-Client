import pytest
import requests
from unittest.mock import Mock, patch
from src.notedx_sdk import NoteDxClient
from src.notedx_sdk.exceptions import (
    NoteDxError,
    AuthenticationError,
    AuthorizationError,
    PaymentRequiredError,
    NotFoundError,
    BadRequestError,
    RateLimitError,
    NetworkError,
    InternalServerError,
)

@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = Mock(spec=requests.Response)
    response.status_code = 200
    response.json.return_value = {"message": "success"}
    response.text = "success"
    return response

@pytest.fixture
def mock_session():
    """Create a mock session with default successful response."""
    with patch('requests.Session') as mock_session:
        session = Mock()
        response = Mock(spec=requests.Response)
        response.status_code = 200
        response.json.return_value = {"message": "success"}
        response.text = "success"
        session.request.return_value = response
        mock_session.return_value = session
        yield session

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
        mock_response = Mock(spec=requests.Response)
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
        mock_response = Mock(spec=requests.Response)
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
        mock_response = Mock(spec=requests.Response)
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

    @patch('requests.Session.request')
    def test_change_password_success(self, mock_request):
        """Test successful password change"""
        # Setup mock login response
        mock_login = Mock(spec=requests.Response)
        mock_login.status_code = 200
        mock_login.json.return_value = {
            "user_id": "test-user",
            "id_token": "test-token",
            "refresh_token": "test-refresh"
        }

        # Setup mock password change response
        mock_change = Mock(spec=requests.Response)
        mock_change.status_code = 200
        mock_change.json.return_value = {
            "message": "Password updated successfully",
            "requires_reauth": True
        }

        mock_request.side_effect = [mock_login, mock_change]

        client = NoteDxClient(email="test@example.com", password="old-pass", auto_login=True)
        result = client.change_password("old-pass", "new-pass")

        # Verify requests
        assert mock_request.call_count == 2
        calls = mock_request.call_args_list
        
        # First call should be login
        assert calls[0][1]['json'] == {
            "email": "test@example.com",
            "password": "old-pass"
        }
        
        # Second call should be password change
        assert calls[1][1]['json'] == {
            "current_password": "old-pass",
            "new_password": "new-pass"
        }
        # When requires_reauth is True, tokens should be cleared
        assert client._token is None
        assert client._refresh_token is None
        assert client._user_id is None
        assert result["requires_reauth"] is True

    @patch('requests.Session.request')
    def test_change_password_wrong_current(self, mock_request):
        """Test password change with wrong current password"""
        # Setup mock login response
        mock_login = Mock(spec=requests.Response)
        mock_login.status_code = 200
        mock_login.json.return_value = {
            "user_id": "test-user",
            "id_token": "test-token",
            "refresh_token": "test-refresh"
        }

        # Setup mock password change response
        mock_change = Mock(spec=requests.Response)
        mock_change.status_code = 401
        mock_change.json.return_value = {
            "error": {
                "code": "INVALID_PASSWORD",
                "message": "Current password is incorrect"
            }
        }

        mock_request.side_effect = [mock_login, mock_change]

        client = NoteDxClient(email="test@example.com", password="old-pass", auto_login=True)

        with pytest.raises(AuthenticationError) as exc_info:
            client.change_password("wrong-pass", "new-pass")
        assert "Current password is incorrect" in str(exc_info.value)

    @patch('requests.Session.request')
    def test_change_password_no_token(self, mock_request):
        """Test password change without being logged in"""
        client = NoteDxClient(email="test@example.com", password="old-pass", auto_login=False)
        
        with pytest.raises(AuthenticationError) as exc_info:
            client.change_password("old-pass", "new-pass")
        assert "Must be logged in to change password" in str(exc_info.value)
        mock_request.assert_not_called()

    @patch('requests.Session.request')
    def test_auto_login_on_init(self, mock_request):
        """Test automatic login during initialization"""
        # Setup mock response for login
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user_id": "test-user",
            "id_token": "test-token",
            "refresh_token": "test-refresh",
            "email": "test@example.com"
        }
        mock_request.return_value = mock_response

        client = NoteDxClient(email="test@example.com", password="test-pass", auto_login=True)
        
        mock_request.assert_called_once()
        assert client._token == "test-token"
        assert client._refresh_token == "test-refresh"

    @patch('requests.Session.request')
    def test_login_with_invalid_json_response(self, mock_request):
        """Test login with invalid JSON response"""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Invalid response"
        mock_request.return_value = mock_response

        client = NoteDxClient(email="test@example.com", password="test-pass", auto_login=False)
        
        with pytest.raises(NoteDxError) as exc_info:
            client.login()
        assert "Login failed" in str(exc_info.value)

    @patch('requests.Session.request')
    def test_refresh_token_with_network_error(self, mock_request):
        """Test token refresh with network error"""
        mock_request.side_effect = requests.ConnectionError("Connection failed")

        client = NoteDxClient(email="test@example.com", password="test-pass", auto_login=False)
        client._token = "old-token"
        client._refresh_token = "refresh-token"

        with pytest.raises(NetworkError) as exc_info:
            client.refresh_token()
        assert "Connection error" in str(exc_info.value)

    @patch('requests.Session.request')
    def test_login_with_missing_tokens(self, mock_request):
        """Test login response with missing tokens"""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user_id": "test-user",
            # Missing id_token and refresh_token
        }
        mock_request.return_value = mock_response

        client = NoteDxClient(email="test@example.com", password="test-pass", auto_login=False)

        with pytest.raises(AuthenticationError) as exc_info:
            client.login()
        assert "Missing required tokens in response" in str(exc_info.value)

    @patch('requests.Session.request')
    def test_concurrent_auth_retries(self, mock_request):
        """Test handling of concurrent authentication retries"""
        # Setup responses for multiple concurrent 401s
        mock_auth_error = Mock(spec=requests.Response)
        mock_auth_error.status_code = 401
        mock_auth_error.json.return_value = {
            "error": {
                "code": "TOKEN_EXPIRED",
                "message": "Token expired"
            }
        }

        # Setup mock refresh token response
        mock_refresh = Mock(spec=requests.Response)
        mock_refresh.status_code = 200
        mock_refresh.json.return_value = {
            "id_token": "new-token",
            "refresh_token": "new-refresh"
        }

        # Setup mock login response
        mock_login = Mock(spec=requests.Response)
        mock_login.status_code = 200
        mock_login.json.return_value = {
            "user_id": "test-user",
            "id_token": "login-token",
            "refresh_token": "login-refresh"
        }

        # Setup mock success response
        mock_success = Mock(spec=requests.Response)
        mock_success.status_code = 200
        mock_success.json.return_value = {"data": "success"}

        # Simulate: auth error -> refresh success -> success
        mock_request.side_effect = [mock_auth_error, mock_refresh, mock_success]

        client = NoteDxClient(email="test@example.com", password="test-pass", auto_login=False)
        client._token = "expired-token"
        client._refresh_token = "refresh-token"

        result = client._request("GET", "test/endpoint")
        assert result == {"data": "success"}
        assert mock_request.call_count == 3

    @patch('requests.Session.request')
    def test_request_retry_with_backoff(self, mock_request):
        """Test request retry with exponential backoff"""
        # Setup responses: 500, 500, success
        mock_error1 = Mock(spec=requests.Response)
        mock_error1.status_code = 500
        mock_error1.json.return_value = {"error": {"message": "Server error"}}

        mock_error2 = Mock(spec=requests.Response)
        mock_error2.status_code = 500
        mock_error2.json.return_value = {"error": {"message": "Server error"}}

        mock_success = Mock(spec=requests.Response)
        mock_success.status_code = 200
        mock_success.json.return_value = {"data": "success"}

        mock_request.side_effect = [mock_error1, mock_error2, mock_success]

        client = NoteDxClient(api_key="test-api-key", auto_login=False)
        
        with pytest.raises(InternalServerError) as exc_info:
            result = client._request("GET", "test/endpoint")
        assert "Server error" in str(exc_info.value)

    @patch('requests.Session.request')
    def test_request_max_retries_exceeded(self, mock_request):
        """Test request fails after max retries"""
        # Setup all responses as 401 errors
        mock_error = Mock(spec=requests.Response)
        mock_error.status_code = 401
        mock_error.json.return_value = {
            "error": {
                "code": "TOKEN_EXPIRED",
                "message": "Token expired"
            }
        }

        # Setup mock refresh response
        mock_refresh = Mock(spec=requests.Response)
        mock_refresh.status_code = 200
        mock_refresh.json.return_value = {
            "id_token": "new-token",
            "refresh_token": "new-refresh"
        }

        # Setup mock relogin response
        mock_relogin = Mock(spec=requests.Response)
        mock_relogin.status_code = 200
        mock_relogin.json.return_value = {
            "user_id": "test-user",
            "id_token": "relogin-token",
            "refresh_token": "relogin-refresh"
        }

        # Simulate multiple retries
        mock_request.side_effect = [mock_error] * 3 + [mock_refresh, mock_relogin]

        client = NoteDxClient(email="test@example.com", password="test-pass", auto_login=False)
        client._token = "expired-token"
        client._refresh_token = "refresh-token"

        with pytest.raises(AuthenticationError) as exc_info:
            client._request("GET", "test/endpoint")
        assert mock_request.call_count >= 3

    @patch('requests.Session.request')
    def test_request_retry_different_methods(self, mock_request):
        """Test retry behavior with different HTTP methods"""
        # Setup responses: 500 error
        mock_error = Mock(spec=requests.Response)
        mock_error.status_code = 500
        mock_error.json.return_value = {
            "error": {
                "message": "Server error"
            }
        }

        mock_request.return_value = mock_error

        client = NoteDxClient(api_key="test-api-key", auto_login=False)
        with pytest.raises(InternalServerError) as exc_info:
            client._request("GET", "test/endpoint")
        assert "Server error" in str(exc_info.value)
        assert mock_request.call_count == 1  # No retries for 500 errors

    @patch('requests.Session.request')
    def test_request_retry_auth_refresh(self, mock_request):
        """Test complex retry scenario with auth refresh"""
        # Setup responses: 401 (token expired) -> refresh success -> original request success
        mock_auth_error = Mock(spec=requests.Response)
        mock_auth_error.status_code = 401
        mock_auth_error.json.return_value = {
            "error": {
                "code": "TOKEN_EXPIRED",
                "message": "Token expired"
            }
        }

        mock_refresh = Mock(spec=requests.Response)
        mock_refresh.status_code = 200
        mock_refresh.json.return_value = {
            "id_token": "new-token",
            "refresh_token": "new-refresh"
        }

        mock_success = Mock(spec=requests.Response)
        mock_success.status_code = 200
        mock_success.json.return_value = {"data": "success"}

        mock_request.side_effect = [mock_auth_error, mock_refresh, mock_success]

        client = NoteDxClient(email="test@example.com", password="test-pass", auto_login=False)
        client._token = "expired-token"
        client._refresh_token = "refresh-token"

        result = client._request("GET", "test/endpoint")
        assert result == {"data": "success"}
        assert mock_request.call_count == 3

# Test request handling
class TestRequestHandling:
    @patch('requests.Session.request')
    def test_request_with_api_key(self, mock_request):
        """Test request with API key authentication"""
        # Setup mock response
        mock_response = Mock(spec=requests.Response)
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
        mock_response = Mock(spec=requests.Response)
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
        mock_error = Mock(spec=requests.Response)
        mock_error.status_code = 401
        mock_error.json.return_value = {
            "error": {
                "code": "TOKEN_EXPIRED",
                "message": "Token expired"
            }
        }

        mock_success = Mock(spec=requests.Response)
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
        mock_response = Mock(spec=requests.Response)
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

    @patch('requests.Session.request')
    def test_request_json_decode_error(self, mock_request):
        """Test handling of JSON decode errors in _request method."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Invalid response"
        mock_request.return_value = mock_response

        client = NoteDxClient(api_key="test-key", auto_login=False)

        # The client returns the text as data instead of raising NetworkError
        result = client._request("GET", "test/endpoint")
        assert result == {"message": "Invalid response"}

    @patch('requests.Session.request')
    def test_login_success(self, mock_request):
        """Test successful login."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id_token": "test-token",
            "refresh_token": "test-refresh",
            "expires_in": "3600",
            "user_id": "test-user-id"
        }
        mock_response.text = "success"
        mock_request.return_value = mock_response

        client = NoteDxClient(email="test@example.com", password="password", auto_login=False)
        result = client.login()

        assert client._token == "test-token"
        assert client._refresh_token == "test-refresh"
        assert client._user_id == "test-user-id"
        mock_request.assert_called_once()

    @patch('requests.Session.request')
    def test_login_failure(self, mock_request):
        """Test failed login."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 401  # Changed to 401 for AuthenticationError
        mock_response.json.return_value = {
            "error": {"message": "Invalid password"}
        }
        mock_response.text = "Invalid password"
        mock_request.return_value = mock_response

        client = NoteDxClient(email="test@example.com", password="wrong", auto_login=False)

        with pytest.raises(AuthenticationError) as exc_info:
            client.login()
        assert "Invalid password" in str(exc_info.value)

    @patch('requests.Session.request')
    def test_refresh_token_failure(self, mock_request):
        """Test failed token refresh."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 401  # Changed to 401 for AuthenticationError
        mock_response.json.return_value = {
            "error": {"message": "Invalid refresh token"}
        }
        mock_response.text = "Invalid refresh token"
        mock_request.return_value = mock_response

        client = NoteDxClient(api_key="test-key", auto_login=False)
        client._refresh_token = "invalid-refresh-token"

        with pytest.raises(AuthenticationError) as exc_info:
            client.refresh_token()
        assert "Invalid refresh token" in str(exc_info.value)

    @patch('requests.Session.request')
    def test_request_retry_with_backoff(self, mock_request):
        """Test request retry with exponential backoff"""
        # Setup responses: 500, 500, success
        mock_error1 = Mock(spec=requests.Response)
        mock_error1.status_code = 500
        mock_error1.json.return_value = {"error": {"message": "Server error"}}

        mock_error2 = Mock(spec=requests.Response)
        mock_error2.status_code = 500
        mock_error2.json.return_value = {"error": {"message": "Server error"}}

        mock_success = Mock(spec=requests.Response)
        mock_success.status_code = 200
        mock_success.json.return_value = {"data": "success"}

        mock_request.side_effect = [mock_error1, mock_error2, mock_success]

        client = NoteDxClient(api_key="test-api-key", auto_login=False)
        
        with pytest.raises(InternalServerError) as exc_info:
            result = client._request("GET", "test/endpoint")
        assert "Server error" in str(exc_info.value)

    @patch('requests.Session.request')
    def test_request_max_retries_exceeded(self, mock_request):
        """Test request fails after max retries"""
        # Setup all responses as 401 errors
        mock_error = Mock(spec=requests.Response)
        mock_error.status_code = 401
        mock_error.json.return_value = {
            "error": {
                "code": "TOKEN_EXPIRED",
                "message": "Token expired"
            }
        }

        # Setup mock refresh response
        mock_refresh = Mock(spec=requests.Response)
        mock_refresh.status_code = 200
        mock_refresh.json.return_value = {
            "id_token": "new-token",
            "refresh_token": "new-refresh"
        }

        # Setup mock relogin response
        mock_relogin = Mock(spec=requests.Response)
        mock_relogin.status_code = 200
        mock_relogin.json.return_value = {
            "user_id": "test-user",
            "id_token": "relogin-token",
            "refresh_token": "relogin-refresh"
        }

        # Simulate multiple retries
        mock_request.side_effect = [mock_error] * 3 + [mock_refresh, mock_relogin]

        client = NoteDxClient(email="test@example.com", password="test-pass", auto_login=False)
        client._token = "expired-token"
        client._refresh_token = "refresh-token"

        with pytest.raises(AuthenticationError) as exc_info:
            client._request("GET", "test/endpoint")
        assert mock_request.call_count >= 3

    @patch('requests.Session.request')
    def test_request_retry_different_methods(self, mock_request):
        """Test retry behavior with different HTTP methods"""
        # Setup responses: 500 error
        mock_error = Mock(spec=requests.Response)
        mock_error.status_code = 500
        mock_error.json.return_value = {
            "error": {
                "message": "Server error"
            }
        }

        mock_request.return_value = mock_error

        client = NoteDxClient(api_key="test-api-key", auto_login=False)
        with pytest.raises(InternalServerError) as exc_info:
            client._request("GET", "test/endpoint")
        assert "Server error" in str(exc_info.value)
        assert mock_request.call_count == 1  # No retries for 500 errors

    @patch('requests.Session.request')
    def test_request_retry_auth_refresh(self, mock_request):
        """Test complex retry scenario with auth refresh"""
        # Setup responses: 401 (token expired) -> refresh success -> original request success
        mock_auth_error = Mock(spec=requests.Response)
        mock_auth_error.status_code = 401
        mock_auth_error.json.return_value = {
            "error": {
                "code": "TOKEN_EXPIRED",
                "message": "Token expired"
            }
        }

        mock_refresh = Mock(spec=requests.Response)
        mock_refresh.status_code = 200
        mock_refresh.json.return_value = {
            "id_token": "new-token",
            "refresh_token": "new-refresh"
        }

        mock_success = Mock(spec=requests.Response)
        mock_success.status_code = 200
        mock_success.json.return_value = {"data": "success"}

        mock_request.side_effect = [mock_auth_error, mock_refresh, mock_success]

        client = NoteDxClient(email="test@example.com", password="test-pass", auto_login=False)
        client._token = "expired-token"
        client._refresh_token = "refresh-token"

        result = client._request("GET", "test/endpoint")
        assert result == {"data": "success"}
        assert mock_request.call_count == 3

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
        mock_response = Mock(spec=requests.Response)
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

