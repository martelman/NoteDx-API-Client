import pytest
from unittest.mock import Mock

from src.notedx_sdk.api_keys.key_manager import KeyManager


class TestKeyManager:
    @pytest.fixture
    def mock_client(self):
        return Mock()

    @pytest.fixture
    def key_manager(self, mock_client):
        return KeyManager(mock_client)

    def test_list_api_keys_with_full_details(self, key_manager, mock_client):
        """Test listing API keys with full (unmasked) details"""
        expected_response = [
            {
                "key": "live_key_123",
                "type": "live",
                "status": "active",
                "created_at": "2024-01-01T00:00:00Z",
                "last_used": "2024-01-02T00:00:00Z",
                "metadata": {"env": "production"}
            }
        ]
        mock_client._request.return_value = expected_response
        
        result = key_manager.list_api_keys(show_full=True)
        
        mock_client._request.assert_called_once_with(
            "GET", 
            "user/list-api-keys", 
            params={"showFull": "true"}
        )
        assert result == expected_response

    def test_create_api_key_with_metadata(self, key_manager, mock_client):
        """Test creating a live API key with metadata"""
        metadata = {"env": "production", "purpose": "testing"}
        expected_response = {
            "api_key": "live_key_123",
            "key_type": "live",
            "metadata": metadata
        }
        mock_client._request.return_value = expected_response
        
        result = key_manager.create_api_key(
            key_type="live",
            metadata=metadata
        )
        
        mock_client._request.assert_called_once_with(
            "POST",
            "user/create-api-key",
            data={"keyType": "live", "metadata": metadata}
        )
        assert result == expected_response

    def test_update_metadata(self, key_manager, mock_client):
        """Test updating metadata for an API key"""
        api_key = "live_key_123"
        metadata = {"env": "staging", "updated": "true"}
        expected_response = {
            "message": "API key metadata updated successfully",
            "api_key": api_key
        }
        mock_client._request.return_value = expected_response
        
        result = key_manager.update_metadata(api_key, metadata)
        
        mock_client._request.assert_called_once_with(
            "POST",
            "user/update-api-key-metadata",
            data={"apiKey": api_key, "metadata": metadata}
        )
        assert result == expected_response

    def test_update_status(self, key_manager, mock_client):
        """Test updating API key status"""
        api_key = "live_key_123"
        expected_response = {
            "message": "API key status updated successfully",
            "api_key": api_key,
            "status": "inactive"
        }
        mock_client._request.return_value = expected_response
        
        result = key_manager.update_status(api_key, status="inactive")
        
        mock_client._request.assert_called_once_with(
            "POST",
            f"user/api-keys/{api_key}/status",
            data={"apiKey": api_key, "status": "inactive"}
        )
        assert result == expected_response

    def test_delete_api_key(self, key_manager, mock_client):
        """Test deleting an API key"""
        api_key = "live_key_123"
        expected_response = {
            "message": "API key deleted successfully",
            "api_key": api_key
        }
        mock_client._request.return_value = expected_response
        
        result = key_manager.delete_api_key(api_key)
        
        mock_client._request.assert_called_once_with(
            "DELETE",
            f"user/api-keys/{api_key}",
            data={"apiKey": api_key}
        )
        assert result == expected_response 