import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from src.notedx_sdk.usage.usage_manager import UsageManager
from src.notedx_sdk.exceptions import (
    ValidationError,
)

@pytest.fixture
def mock_client():
    """Create a mock NoteDxClient."""
    client = Mock()
    client._token = "mock-firebase-token"
    return client

@pytest.fixture
def usage_manager(mock_client):
    """Create a UsageManager instance with a mock client."""
    return UsageManager(mock_client)

@pytest.fixture
def mock_usage_response():
    """Sample response for usage statistics."""
    return {
        "period": {
            "start_month": "2024-01",
            "end_month": "2024-01"
        },
        "totals": {
            "jobs": 150,
            "transcription_tokens": 50000,
            "note_tokens": 25000,
            "base_cost": 100.00,
            "final_cost": 85.00,
            "savings": 15.00,
            "effective_discount_percentage": 15.0,
            "free_jobs_left": 50
        },
        "monthly_breakdown": [
            {
                "month": "2024-01",
                "jobs": 150,
                "transcription_tokens": 50000,
                "note_tokens": 25000,
                "base_cost": 100.00,
                "final_cost": 85.00,
                "savings": 15.00,
                "current_tier_discount": 15.0,
                "tiers": {
                    "tier1": 50,
                    "tier2": 50,
                    "tier3": 30,
                    "tier4": 20
                }
            }
        ],
        "api_keys": {
            "sk_live_****1234": {
                "jobs": 100,
                "tokens": {
                    "transcription": 35000,
                    "note_generation": 15000
                },
                "costs": {
                    "base": 70.00,
                    "final": 59.50,
                    "savings": 10.50
                },
                "tiers": {
                    "tier1": 30,
                    "tier2": 30,
                    "tier3": 20,
                    "tier4": 20
                }
            },
            "sk_test_****5678": {
                "jobs": 50,
                "tokens": {
                    "transcription": 15000,
                    "note_generation": 10000
                },
                "costs": {
                    "base": 30.00,
                    "final": 25.50,
                    "savings": 4.50
                },
                "tiers": {
                    "tier1": 20,
                    "tier2": 20,
                    "tier3": 10,
                    "tier4": 0
                }
            }
        }
    }

class TestUsageManager:
    def test_init(self, usage_manager):
        """Test UsageManager initialization."""
        assert usage_manager._client is not None
        assert usage_manager.logger is not None

    @pytest.mark.parametrize(
        "month,param_name,should_raise",
        [
            ("2024-01", "start_month", False),
            ("2024-12", "end_month", False),
            ("2024-1", "start_month", True),
            ("2024-13", "end_month", True),
            ("2024/01", "start_month", True),
            ("invalid", "end_month", True),
            ("", "start_month", True),
        ]
    )
    def test_validate_month_format(self, usage_manager, month, param_name, should_raise):
        """Test month format validation with various inputs."""
        if should_raise:
            with pytest.raises(ValidationError) as exc_info:
                usage_manager._validate_month_format(month, param_name)
            assert "Invalid" in str(exc_info.value)
            assert param_name in str(exc_info.value)
        else:
            usage_manager._validate_month_format(month, param_name)

    def test_get_current_month_usage(self, usage_manager, mock_usage_response):
        """Test getting usage stats for current month (default behavior)."""
        usage_manager._client._request.return_value = mock_usage_response
        current_month = datetime.now(timezone.utc).strftime('%Y-%m')

        result = usage_manager.get()

        usage_manager._client._request.assert_called_once_with(
            "GET", "user/usage", params={'start_month': current_month, 'end_month': current_month}
        )
        assert result == mock_usage_response
        assert result["totals"]["jobs"] == 150
        assert result["totals"]["free_jobs_left"] == 50
        assert len(result["monthly_breakdown"]) == 1
        assert len(result["api_keys"]) == 2

    @pytest.mark.parametrize(
        "start_month,end_month,expected_params",
        [
            ("2024-01", "2024-03", {"start_month": "2024-01", "end_month": "2024-03"}),
            ("2024-01", None, {"start_month": "2024-01"}),
            (None, "2024-12", {"end_month": "2024-12"}),
        ]
    )
    def test_get_usage_with_date_range(self, usage_manager, mock_usage_response, 
                                     start_month, end_month, expected_params):
        """Test getting usage stats with different date ranges."""
        usage_manager._client._request.return_value = mock_usage_response

        result = usage_manager.get(start_month=start_month, end_month=end_month)

        usage_manager._client._request.assert_called_once_with(
            "GET", "user/usage", params=expected_params
        )
        assert result == mock_usage_response

    def test_get_usage_invalid_date_range(self, usage_manager):
        """Test getting usage stats with invalid date range."""
        with pytest.raises(ValidationError) as exc_info:
            usage_manager.get(start_month="2024-03", end_month="2024-01")
        assert "Invalid date range" in str(exc_info.value)
        assert "must be <=" in str(exc_info.value)

    def test_get_usage_network_error(self, usage_manager):
        """Test handling of network errors when getting usage stats."""
        usage_manager._client._request.side_effect = Exception("Connection failed")

        with pytest.raises(Exception) as exc_info:
            usage_manager.get()
        assert "Connection failed" in str(exc_info.value)

    def test_get_usage_detailed_validation(self, usage_manager, mock_usage_response):
        """Test detailed validation of usage response structure."""
        usage_manager._client._request.return_value = mock_usage_response
        result = usage_manager.get(start_month="2024-01", end_month="2024-01")

        # Validate period
        assert "period" in result
        assert result["period"]["start_month"] == "2024-01"
        assert result["period"]["end_month"] == "2024-01"

        # Validate totals
        totals = result["totals"]
        assert totals["jobs"] == 150
        assert totals["transcription_tokens"] == 50000
        assert totals["note_tokens"] == 25000
        assert totals["base_cost"] == 100.00
        assert totals["final_cost"] == 85.00
        assert totals["savings"] == 15.00

        # Validate monthly breakdown
        monthly = result["monthly_breakdown"][0]
        assert monthly["month"] == "2024-01"
        assert monthly["jobs"] == 150
        assert "tiers" in monthly
        assert sum(monthly["tiers"].values()) == monthly["jobs"]

        # Validate API keys
        api_keys = result["api_keys"]
        assert len(api_keys) == 2
        for key_stats in api_keys.values():
            assert "jobs" in key_stats
            assert "tokens" in key_stats
            assert "costs" in key_stats
            assert "tiers" in key_stats
