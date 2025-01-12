import pytest
import os
import requests
from unittest.mock import patch, MagicMock, Mock

from src.notedx_sdk import NoteDxClient
from src.notedx_sdk.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NetworkError,
    RateLimitError,
    NotFoundError,
    InternalServerError,
    ValidationError,
    InvalidFieldError
)

TEST_BASE_URL = "https://api.notedx.io/v1"

# Basic initialization tests
def test_client_initialization():
    """Test basic client initialization with API key."""
    client = NoteDxClient(api_key="test_key")
    assert isinstance(client, NoteDxClient)
    assert client._api_key == "test_key"
    assert client.base_url == NoteDxClient.BASE_URL

def test_client_initialization_no_key():
    """Test client initialization without API key raises error."""
    with pytest.raises(AuthenticationError):
        NoteDxClient(api_key=None)

def test_client_initialization_with_email_password():
    """Test client initialization with email and password."""
    client = NoteDxClient(
        email="test@example.com",
        password="test_password",
        auto_login=False
    )
    assert isinstance(client, NoteDxClient)
    assert client._email == "test@example.com"
    assert client._password == "test_password"
    assert client.base_url == NoteDxClient.BASE_URL

def test_set_api_key():
    """Test setting API key after initialization."""
    client = NoteDxClient(api_key="initial_key")
    client.set_api_key("new_key")
    assert client._api_key == "new_key"

# Environment variable tests
@pytest.fixture
def mock_env_vars():
    """Fixture to set and clean up environment variables."""
    original_env = dict(os.environ)
    os.environ["NOTEDX_EMAIL"] = "env_test@example.com"
    os.environ["NOTEDX_PASSWORD"] = "env_password"
    os.environ["NOTEDX_API_KEY"] = "env_api_key"
    
    yield
    
    os.environ.clear()
    os.environ.update(original_env)

def test_client_initialization_from_env(mock_env_vars):
    """Test client initialization using environment variables."""
    client = NoteDxClient(auto_login=False)
    assert client._email == "env_test@example.com"
    assert client._password == "env_password"
    assert client._api_key == "env_api_key"

# Authentication tests
@pytest.fixture
def mock_session():
    """Fixture to mock requests.Session."""
    with patch("requests.Session") as mock:
        yield mock.return_value

def test_successful_login(mock_session):
    """Test successful login flow."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id_token": "test_token",
        "refresh_token": "test_refresh_token",
        "user_id": "test_user_id"
    }
    mock_session.post.return_value = mock_response

    client = NoteDxClient(
        email="test@example.com",
        password="test_password",
        session=mock_session
    )

    assert client._token == "test_token"
    assert client._refresh_token == "test_refresh_token"
    mock_session.post.assert_called_once()

def test_failed_login(mock_session):
    """Test failed login with invalid credentials."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {
        "message": "Invalid credentials",
        "error": {"code": "AUTH_FAILED"}
    }
    mock_session.post.return_value = mock_response

    with pytest.raises(AuthenticationError) as exc_info:
        client = NoteDxClient(
            email="wrong@example.com",
            password="wrong_password",
            session=mock_session
        )
    
    assert "Invalid credentials" in str(exc_info.value)

def test_manual_token_setting():
    """Test manually setting tokens."""
    client = NoteDxClient(api_key="test_key")
    client.set_token("manual_token", "manual_refresh")
    assert client._token == "manual_token"
    assert client._refresh_token == "manual_refresh"

# Request handling tests
@pytest.mark.parametrize("status_code,exception_class,error_msg", [
    (401, AuthenticationError, "Invalid API Key"),
    (403, AuthorizationError, "Forbidden"),
    (404, NotFoundError, "Resource not found"),
    (429, RateLimitError, "API rate limit exceeded"),
    (500, InternalServerError, "Internal server error"),
])
def test_request_error_handling(mock_session, status_code, exception_class, error_msg):
    """Test various error responses from the API."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = {
        "message": error_msg,
        "error": {"code": "ERROR_CODE"}
    }
    mock_session.request.return_value = mock_response

    client = NoteDxClient(api_key="test_key", session=mock_session)

    with pytest.raises(exception_class) as exc_info:
        client._request("GET", "/test")
    
    assert error_msg in str(exc_info.value)

def test_network_timeout(mock_session):
    """Test handling of network timeouts."""
    mock_session.request.side_effect = requests.Timeout("Connection timed out")
    
    client = NoteDxClient(api_key="test_key", session=mock_session)
    
    with pytest.raises(NetworkError) as exc_info:
        client._request("GET", "/test")
    
    assert "timed out" in str(exc_info.value)

def test_connection_error(mock_session):
    """Test handling of connection errors."""
    mock_session.request.side_effect = requests.ConnectionError("Connection failed")
    
    client = NoteDxClient(api_key="test_key", session=mock_session)
    
    with pytest.raises(NetworkError) as exc_info:
        client._request("GET", "/test")
    
    assert "Connection error" in str(exc_info.value)

def test_successful_request(mock_session):
    """Test successful API request."""
    expected_data = {"key": "value"}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = expected_data
    mock_session.request.return_value = mock_response

    client = NoteDxClient(api_key="test_key", session=mock_session)
    result = client._request("GET", "/test")

    assert result == expected_data
    mock_session.request.assert_called_once()

# URL handling tests
def test_base_url_trailing_slash():
    """Test that base_url handles trailing slashes correctly."""
    client1 = NoteDxClient(base_url=TEST_BASE_URL + "/", api_key="test_key")
    client2 = NoteDxClient(base_url=TEST_BASE_URL, api_key="test_key")
    
    assert client1.base_url == client2.base_url
    assert not client1.base_url.endswith("/")

@pytest.mark.parametrize("endpoint,expected", [
    ("/test", "/test"),
    ("test", "/test"),
    ("/test/", "/test"),
    ("test/", "/test"),
])
def test_endpoint_slash_handling(mock_session, endpoint, expected):
    """Test that endpoint slashes are handled correctly."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_session.request.return_value = mock_response

    client = NoteDxClient(api_key="test_key", session=mock_session)
    client._request("GET", endpoint)

    called_url = mock_session.request.call_args[1]["url"]
    assert called_url == f"{TEST_BASE_URL}{expected}" 

class TestClient:
    def test_update_account_no_fields(self, mock_client):
        with pytest.raises(InvalidFieldError, match="At least one of these fields must be provided: company_name, contact_email, phone_number, address"):
            mock_client.account.update_account()

    @patch('os.path.isfile')
    @patch('builtins.open')
    def test_validate_audio_file_invalid_format(self, mock_open, mock_isfile, mock_client):
        mock_isfile.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = b'test'
        with pytest.raises(ValidationError, match="Unsupported audio format"):
            mock_client.notes._validate_audio_file("test.txt")

    @patch('os.path.isfile')
    def test_validate_audio_file_missing_path(self, mock_isfile, mock_client):
        mock_isfile.return_value = False
        with pytest.raises(ValidationError, match="Audio file not found"):
            mock_client.notes._validate_audio_file("test.mp3")

    @patch('os.path.isfile')
    @patch('builtins.open')
    def test_validate_audio_file_success(self, mock_open, mock_isfile, mock_client):
        mock_isfile.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = b'test'
        mock_client.notes._validate_audio_file("test.mp3") 

def test_refresh_token_success(mock_client):
    """Test successful token refresh"""
    mock_client._refresh_token = "old_refresh_token"
    expected_response = {
        "id_token": "new_id_token",
        "refresh_token": "new_refresh_token",
        "user_id": "user123",
        "email": "test@example.com"
    }
    
    with patch.object(mock_client, '_request') as mock_request:
        mock_request.return_value = expected_response
        result = mock_client.refresh_token()
    
    mock_request.assert_called_once_with(
        "POST",
        "auth/refresh",
        data={"refresh_token": "old_refresh_token"}
    )
    assert result == expected_response
    assert mock_client._token == "new_id_token"
    assert mock_client._refresh_token == "new_refresh_token"

def test_refresh_token_no_refresh_token(mock_client):
    """Test refresh token failure when no refresh token is available"""
    mock_client._refresh_token = None
    
    with pytest.raises(AuthenticationError, match="No refresh token available"):
        mock_client.refresh_token()

def test_set_token(mock_client):
    """Test manually setting tokens"""
    mock_client.set_token("new_token", "new_refresh_token")
    
    assert mock_client._token == "new_token"
    assert mock_client._refresh_token == "new_refresh_token"

def test_set_api_key(mock_client):
    """Test setting API key"""
    mock_client.set_api_key("new_api_key")
    
    assert mock_client._api_key == "new_api_key"

def test_handle_auth_retry_success(mock_client):
    """Test successful authentication retry"""
    endpoint = "test/endpoint"
    mock_client._auth_retry_counts[endpoint] = 0
    mock_client._token = "old_token"
    mock_client._email = "test@example.com"
    mock_client._password = "test_password"

    mock_login_response = {
        "id_token": "new_token",
        "user_id": "user123"
    }

    def mock_login():
        mock_client._token = mock_login_response["id_token"]
        return mock_login_response

    with patch.object(mock_client, 'login', side_effect=mock_login) as mock_login_fn:
        result = mock_client._handle_auth_retry(
            endpoint=endpoint,
            error_msg="Token expired",
            error_code="TOKEN_EXPIRED",
            response_data={"error": "Token expired"}
        )

    assert result is True
    assert mock_client._token == "new_token"
    assert mock_client._auth_retry_counts[endpoint] == 1

def test_handle_auth_retry_max_retries(mock_client):
    """Test auth retry when max retries exceeded"""
    endpoint = "test/endpoint"
    mock_client._auth_retry_counts[endpoint] = mock_client.MAX_AUTH_RETRIES

    with pytest.raises(AuthenticationError, match=f"Authorization failed after {mock_client.MAX_AUTH_RETRIES} retries"):
        mock_client._handle_auth_retry(
            endpoint=endpoint,
            error_msg="Token expired",
            error_code="TOKEN_EXPIRED",
            response_data={"error": "Token expired"}
        )

def test_maybe_login_with_existing_token(mock_client):
    """Test _maybe_login when token already exists"""
    mock_login = Mock()
    
    with patch.object(mock_client, 'login', mock_login):
        mock_client._token = "existing_token"
        mock_client._maybe_login()
        # Should not attempt to login since token exists
        mock_login.assert_not_called()

def test_maybe_login_no_credentials(mock_client):
    """Test _maybe_login with no credentials"""
    mock_login = Mock()
    
    with patch.object(mock_client, 'login', mock_login):
        mock_client._token = None
        mock_client._email = None
        mock_client._password = None
        
        mock_client._maybe_login()
        # Should not attempt to login since no credentials
        mock_login.assert_not_called() 