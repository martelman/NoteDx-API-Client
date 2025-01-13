import pytest
from unittest.mock import Mock, patch
from src.notedx_sdk import NoteDxClient

TEST_BASE_URL = "https://api.notedx.io/v1"

@pytest.fixture
def api_key():
    return "test-api-key"

@pytest.fixture
def mock_client(api_key):
    """Create a mock client with request mocking"""
    with patch('requests.Session.request') as mock_request:
        client = NoteDxClient(api_key=api_key, auto_login=False)
        # Mock the _request method to avoid real HTTP calls
        client._request = Mock()
        return client

@pytest.fixture
def mock_response():
    return {
        "message": "Operation completed successfully",
        "status": "success"
    }

@pytest.fixture
def mock_error_response():
    return {
        "message": "An error occurred",
        "status": "error",
        "details": {
            "code": "ERROR_CODE",
            "field": "field_name"
        }
    }

@pytest.fixture
def mock_job_id():
    return "test-job-id"

@pytest.fixture
def mock_presigned_url():
    return "https://storage.example.com/test-file.mp3?token=xyz" 