import pytest
from unittest.mock import Mock
from notedx_sdk import NoteDxClient

TEST_BASE_URL = "https://api.notedx.io/v1"

@pytest.fixture
def api_key():
    return "test-api-key"

@pytest.fixture
def mock_client(api_key):
    client = NoteDxClient(api_key=api_key, base_url=TEST_BASE_URL)
    client._request = Mock()  # Mock the _request method
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