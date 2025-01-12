import pytest
from unittest.mock import patch

from notedx_sdk.exceptions import (
    AuthenticationError,
    ValidationError,
    InactiveAccountError
)

@pytest.mark.unit
class TestUsageManager:
    @patch('requests.request')
    def test_get_usage_success(self, mock_request, mock_client):
        mock_client._request.return_value = {
            "total_minutes": 60,
            "total_notes": 25,
            "period_start": "2024-01",
            "period_end": "2024-01",
            "daily_usage": [
                {
                    "date": "2024-01-01",
                    "minutes": 30,
                    "notes": 12
                },
                {
                    "date": "2024-01-02",
                    "minutes": 30,
                    "notes": 13
                }
            ]
        }

        response = mock_client.usage.get()
        assert response["total_minutes"] == 60
        assert response["total_notes"] == 25
        assert response["period_start"] == "2024-01"
        assert response["period_end"] == "2024-01"
        assert len(response["daily_usage"]) == 2

    @patch('requests.request')
    def test_get_usage_with_dates(self, mock_request, mock_client):
        mock_client._request.return_value = {
            "total_minutes": 120,
            "total_notes": 50,
            "period_start": "2024-01",
            "period_end": "2024-02",
            "daily_usage": []
        }

        response = mock_client.usage.get(start_month="2024-01", end_month="2024-02")
        assert response["total_minutes"] == 120
        assert response["total_notes"] == 50
        assert response["period_start"] == "2024-01"
        assert response["period_end"] == "2024-02"

    @patch('requests.request')
    def test_get_usage_invalid_dates(self, mock_request, mock_client):
        mock_client._request.side_effect = ValidationError("Invalid date format")
        with pytest.raises(ValidationError):
            mock_client.usage.get(start_month="invalid", end_month="invalid")

    @patch('requests.request')
    def test_get_usage_unauthorized(self, mock_request, mock_client):
        mock_client._request.side_effect = AuthenticationError("Missing Authentication Token")
        with pytest.raises(AuthenticationError):
            mock_client.usage.get()

    @patch('requests.request')
    def test_get_usage_inactive_account(self, mock_request, mock_client):
        mock_client._request.side_effect = InactiveAccountError("Account is inactive")
        with pytest.raises(InactiveAccountError):
            mock_client.usage.get() 