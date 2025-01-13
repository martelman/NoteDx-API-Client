import pytest
from unittest.mock import Mock, patch
from src.notedx_sdk.api_keys.key_manager import KeyManager


@pytest.fixture
def mock_client():
    """Create a mock NoteDxClient."""
    client = Mock()
    client._token = "mock-firebase-token"
    return client

@pytest.fixture
def key_manager(mock_client):
    """Create a KeyManager instance with a mock client."""
    return KeyManager(mock_client)

@pytest.fixture
def mock_api_key():
    """Sample API key for testing."""
    return "test-api-key-12345"

@pytest.fixture
def mock_key_list_response():
    """Sample response for list_api_keys."""
    return [
        {
            "key": "sk_test_****1234",
            "type": "sandbox",
            "status": "active",
            "created_at": "2024-01-01T00:00:00Z",
            "last_used": "2024-01-02T00:00:00Z",
        },
        {
            "key": "sk_live_****5678",
            "type": "live",
            "status": "active",
            "created_at": "2024-01-01T00:00:00Z",
            "last_used": "2024-01-02T00:00:00Z",
            "metadata": {"env": "production"}
        }
    ]

class TestKeyManager:
    def test_init(self, key_manager):
        """Test KeyManager initialization."""
        assert key_manager._client is not None
        assert key_manager.logger is not None

    @pytest.mark.parametrize("show_full", [True, False])
    def test_list_api_keys(self, key_manager, mock_key_list_response, show_full):
        """Test listing API keys with and without full details."""
        key_manager._client._request.return_value = mock_key_list_response
        expected_params = {'showFull': 'true'} if show_full else None

        result = key_manager.list_api_keys(show_full=show_full)

        key_manager._client._request.assert_called_once_with(
            "GET", "user/list-api-keys", params=expected_params
        )
        assert result == mock_key_list_response
        assert len(result) == 2
        assert result[0]["type"] == "sandbox"
        assert result[1]["type"] == "live"

    @pytest.mark.parametrize(
        "key_type,metadata,expected_payload",
        [
            (
                "sandbox",
                None,
                {"keyType": "sandbox", "metadata": None}
            ),
            (
                "live",
                {"env": "production", "team": "backend"},
                {"keyType": "live", "metadata": {"env": "production", "team": "backend"}}
            )
        ]
    )
    def test_create_api_key(self, key_manager, key_type, metadata, expected_payload):
        """Test API key creation with different types and metadata."""
        expected_response = {
            "api_key": "sk_test_new12345",
            "key_type": key_type,
            "metadata": metadata
        }
        key_manager._client._request.return_value = expected_response

        result = key_manager.create_api_key(key_type=key_type, metadata=metadata)

        key_manager._client._request.assert_called_once_with(
            "POST",
            "user/create-api-key",
            data=expected_payload
        )
        assert result == expected_response

    def test_update_metadata(self, key_manager, mock_api_key):
        """Test updating API key metadata."""
        new_metadata = {"env": "staging", "owner": "team-a"}
        expected_response = {
            "message": "API key metadata updated successfully",
            "api_key": mock_api_key
        }
        key_manager._client._request.return_value = expected_response

        result = key_manager.update_metadata(mock_api_key, new_metadata)

        key_manager._client._request.assert_called_once_with(
            "POST",
            "user/update-api-key-metadata",
            data={"apiKey": mock_api_key, "metadata": new_metadata}
        )
        assert result == expected_response

    @pytest.mark.parametrize(
        "status",
        ["active", "inactive"]
    )
    def test_update_status(self, key_manager, mock_api_key, status):
        """Test updating API key status."""
        expected_response = {
            "message": "API key status updated successfully",
            "api_key": mock_api_key,
            "status": status
        }
        key_manager._client._request.return_value = expected_response

        result = key_manager.update_status(mock_api_key, status)

        key_manager._client._request.assert_called_once_with(
            "POST",
            f"user/api-keys/{mock_api_key}/status",
            data={"apiKey": mock_api_key, "status": status}
        )
        assert result == expected_response

    def test_delete_api_key(self, key_manager, mock_api_key):
        """Test API key deletion."""
        expected_response = {
            "message": "API key deleted successfully",
            "api_key": mock_api_key
        }
        key_manager._client._request.return_value = expected_response

        result = key_manager.delete_api_key(mock_api_key)

        key_manager._client._request.assert_called_once_with(
            "POST",
            "user/delete-api-key",
            data={"apiKey": mock_api_key}
        )
        assert result == expected_response
