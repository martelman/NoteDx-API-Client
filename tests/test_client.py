import pytest
import os
import requests
from unittest.mock import patch, MagicMock

from src.notedx_sdk import NoteDxClient
from src.notedx_sdk.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NetworkError,
    RateLimitError,
    NotFoundError,
    BadRequestError,
    InternalServerError
)

TEST_BASE_URL = "https://api.notedx.com/v1"

# Basic initialization tests
def test_client_initialization():
    """Test basic client initialization with API key."""
    client = NoteDxClient(base_url=TEST_BASE_URL, api_key="test_key")
    assert isinstance(client, NoteDxClient)
    assert client._api_key == "test_key"
    assert client.base_url == TEST_BASE_URL

def test_client_initialization_no_key():
    """Test client initialization without API key raises error."""
    with pytest.raises(AuthenticationError):
        NoteDxClient(base_url=TEST_BASE_URL, api_key=None)

def test_client_initialization_with_email_password():
    """Test client initialization with email and password."""
    client = NoteDxClient(
        base_url=TEST_BASE_URL,
        email="test@example.com",
        password="test_password",
        auto_login=False
    )
    assert isinstance(client, NoteDxClient)
    assert client._email == "test@example.com"
    assert client._password == "test_password"
    assert client.base_url == TEST_BASE_URL

def test_set_api_key():
    """Test setting API key after initialization."""
    client = NoteDxClient(base_url=TEST_BASE_URL, api_key="initial_key")
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
    client = NoteDxClient(base_url=TEST_BASE_URL, auto_login=False)
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
        "access_token": "test_token",
        "refresh_token": "test_refresh_token"
    }
    mock_session.post.return_value = mock_response

    client = NoteDxClient(
        base_url=TEST_BASE_URL,
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
            base_url=TEST_BASE_URL,
            email="wrong@example.com",
            password="wrong_password",
            session=mock_session
        )
    
    assert "Invalid credentials" in str(exc_info.value)

def test_manual_token_setting():
    """Test manually setting tokens."""
    client = NoteDxClient(base_url=TEST_BASE_URL, api_key="test_key")
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

    client = NoteDxClient(base_url=TEST_BASE_URL, api_key="test_key", session=mock_session)

    with pytest.raises(exception_class) as exc_info:
        client._request("GET", "/test")
    
    assert error_msg in str(exc_info.value)

def test_network_timeout(mock_session):
    """Test handling of network timeouts."""
    mock_session.request.side_effect = requests.Timeout("Connection timed out")
    
    client = NoteDxClient(base_url=TEST_BASE_URL, api_key="test_key", session=mock_session)
    
    with pytest.raises(NetworkError) as exc_info:
        client._request("GET", "/test")
    
    assert "timed out" in str(exc_info.value)

def test_connection_error(mock_session):
    """Test handling of connection errors."""
    mock_session.request.side_effect = requests.ConnectionError("Connection failed")
    
    client = NoteDxClient(base_url=TEST_BASE_URL, api_key="test_key", session=mock_session)
    
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

    client = NoteDxClient(base_url=TEST_BASE_URL, api_key="test_key", session=mock_session)
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

    client = NoteDxClient(base_url=TEST_BASE_URL, api_key="test_key", session=mock_session)
    client._request("GET", endpoint)

    called_url = mock_session.request.call_args[1]["url"]
    assert called_url == f"{TEST_BASE_URL}{expected}" 