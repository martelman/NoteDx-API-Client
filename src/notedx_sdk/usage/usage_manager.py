from typing import Dict, Any, Optional, List, TYPE_CHECKING
import logging
import re
from datetime import datetime, timezone

from ..exceptions import (
    ValidationError,
    AuthenticationError,
    PaymentRequiredError,
    InactiveAccountError,
    InvalidFieldError
)

if TYPE_CHECKING:
    from ..client import NoteDxClient

# Initialize SDK logger
logger = logging.getLogger("notedx_sdk.usage")
logger.addHandler(logging.NullHandler())  # Default to no handler
logger.setLevel(logging.INFO)  # Default to INFO level

class UsageManager:
    """
    Handles usage data operations for the NoteDx API.
    
    This class provides methods for retrieving and analyzing usage statistics,
    including API calls, note generations, and token usage. It supports
    filtering by date ranges and provides detailed breakdowns by API key and month.
    
    Features:
        - Detailed usage metrics (jobs, tokens)
        - Monthly usage breakdown
        - Per-API key statistics
        - Free tier tracking
    
    Example:
        ```python
        from notedx_sdk import NoteDxClient
        
        # Initialize client
        client = NoteDxClient(
            email="user@example.com",
            password="your-password"
        )
        
        # Get current month's usage
        current = client.usage.get()
        print(f"Total jobs: {current['totals']['jobs']}")
        print(f"Free jobs left: {current['totals']['free_jobs_left']}")
        
        # Get Q1 2024 usage with detailed breakdown
        q1_usage = client.usage.get(
            start_month="2024-01",
            end_month="2024-03"
        )
        
        # Analyze monthly trends
        for month in q1_usage['monthly_breakdown']:
            print(f"Month: {month['month']}")
            print(f"Jobs: {month['jobs']}")
            print(f"Total tokens: {month['total_tokens']}")
            
        # Check API key performance
        for key, stats in q1_usage['api_keys'].items():
            print(f"\nAPI Key: {key}")
            print(f"Jobs: {stats['jobs']}")
            print(f"Transcription tokens: {stats['tokens']['transcription']}")
            print(f"Note tokens: {stats['tokens']['note_generation']}")
            print(f"Usage percentage: {stats['usage_percentage']}%")
        ```
    """
    
    # Date format regex for YYYY-MM validation
    _DATE_FORMAT_REGEX = re.compile(r'^\d{4}-(0[1-9]|1[0-2])$')
    
    def __init__(self, client: "NoteDxClient") -> None:
        """
        Initialize the usage manager.
        
        Args:
            client: The parent NoteDxClient instance
        """
        self._client = client
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.debug("Initialized UsageManager")

    def _validate_month_format(self, month: str, param_name: str) -> None:
        """
        Validate that a month string matches the required YYYY-MM format.
        
        Args:
            month (str): Month string to validate
            param_name (str): Parameter name for error messages
            
        Raises:
            ValidationError: If the month format is invalid
        """
        if not self._DATE_FORMAT_REGEX.match(month):
            raise ValidationError(
                f"Invalid {param_name} format: {month}. Must be in YYYY-MM format (e.g., 2024-01)"
            )

    def get(self, start_month: Optional[str] = None, end_month: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve detailed usage statistics for the authenticated account.

        ```bash
        GET /user/usage
        ```

        Wraps the /user/usage endpoint to provide comprehensive usage data including API calls,
        note generations, and token usage. Supports optional date range filtering
        and provides breakdowns by month and API key.

        If no date range is specified, returns data for the current month.

        Args:
            start_month (str, optional): Start month in YYYY-MM format (e.g., "2024-01").
                If not provided, defaults to current month.
            end_month (str, optional): End month in YYYY-MM format (e.g., "2024-01").
                If not provided, defaults to current month.
                Must be >= start_month if both are provided.

        Returns:
            Dict[str, Any]: Comprehensive usage statistics containing:
                period (Dict):

                    - start_month (str): Start of period (YYYY-MM)
                    - end_month (str): End of period (YYYY-MM)
                
                totals (Dict):

                    - jobs (int): Total number of jobs processed
                    - transcription_tokens (int): Total transcription tokens used
                    - note_tokens (int): Total note generation tokens used
                    - total_tokens (int): Total tokens used
                    - free_jobs_left (int): Remaining free tier jobs
                
                monthly_breakdown (List[Dict]): Per-month statistics:

                    - month (str): Month in YYYY-MM format
                    - jobs (int): Jobs processed that month
                    - transcription_tokens (int): Transcription tokens used
                    - note_tokens (int): Note generation tokens used
                    - total_tokens (int): Total tokens used
                
                api_keys (Dict[str, Dict]): Per-API key statistics:

                    - jobs (int): Total jobs for this key
                    - tokens (Dict): Token usage breakdown
                        - transcription (int): Transcription tokens used
                        - note_generation (int): Note generation tokens used
                        - total (int): Total tokens used
                    - usage_percentage (float): Percentage of total token usage
                
                billing (Dict): Current billing period information:

                    - current_usage_amount (float): Current usage amount in USD
                    - billing_period_start (str): Start of billing period (ISO format)
                    - billing_period_end (str): End of billing period (ISO format)
                    - subscription_status (str): Current subscription status

        Raises:
            ValidationError: If date format is invalid (must be YYYY-MM)
            AuthenticationError: If not authenticated or API key is invalid
            PaymentRequiredError: If payment is required
            InactiveAccountError: If account is inactive
            NetworkError: If connection fails
            NoteDxError: For other API errors

        Example:
            ```python
            # Get current month's usage
            current = client.usage.get()
            
            # Check overall metrics
            print(f"Total jobs: {current['totals']['jobs']}")
            print(f"Total tokens: {current['totals']['total_tokens']}")
            print(f"Free jobs remaining: {current['totals']['free_jobs_left']}")
            
            # Analyze API key performance
            for key, stats in current['api_keys'].items():
                print(f"\nAPI Key: {key}")
                print(f"Jobs: {stats['jobs']}")
                print(f"Transcription tokens: {stats['tokens']['transcription']}")
                print(f"Note tokens: {stats['tokens']['note_generation']}")
                print(f"Usage percentage: {stats['usage_percentage']}%")
                
            # Check billing status
            billing = current['billing']
            print(f"\nCurrent usage: ${billing['current_usage_amount']:.2f}")
            print(f"Subscription status: {billing['subscription_status']}")
            ```
        """
        # Set default time period to current month if not specified
        if not start_month and not end_month:
            current_month = datetime.now(timezone.utc).strftime('%Y-%m')
            start_month = current_month
            end_month = current_month
            self.logger.debug("No date range specified, defaulting to current month", 
                            extra={'month': current_month})
        
        # Validate date formats if provided
        if start_month:
            self._validate_month_format(start_month, "start_month")
        if end_month:
            self._validate_month_format(end_month, "end_month")
            
        # Validate date range if both dates provided
        if start_month and end_month and start_month > end_month:
            raise ValidationError(
                f"Invalid date range: start_month ({start_month}) must be <= end_month ({end_month})"
            )

        self.logger.debug(
            "Retrieving usage statistics",
            extra={
                'date_range': {
                    'start_month': start_month,
                    'end_month': end_month
                }
            }
        )

        # Prepare query parameters
        params = {}
        if start_month:
            params['start_month'] = start_month
        if end_month:
            params['end_month'] = end_month

        try:
            response = self._client._request("GET", "user/usage", params=params)
            
            # Log success with summary metrics
            self.logger.info(
                "Successfully retrieved usage statistics",
                extra={
                    'period': response.get('period', {}),
                    'total_jobs': response.get('totals', {}).get('jobs', 0),
                    'total_tokens': response.get('totals', {}).get('total_tokens', 0),
                    'months_retrieved': len(response.get('monthly_breakdown', [])),
                    'api_keys_count': len(response.get('api_keys', {}))
                }
            )
            return response
            
        except ValidationError as e:
            self.logger.error(
                "Invalid date format in usage request",
                extra={
                    'error_type': 'ValidationError',
                    'start_month': start_month,
                    'end_month': end_month,
                    'details': getattr(e, 'details', {})
                },
                exc_info=True
            )
            raise InvalidFieldError(str(e), getattr(e, 'code', None), getattr(e, 'details', {}))

        except AuthenticationError as e:
            self.logger.error(
                "Authentication failed while retrieving usage statistics",
                extra={
                    'error_type': 'AuthenticationError',
                    'code': getattr(e, 'code', None),
                    'details': getattr(e, 'details', {})
                },
                exc_info=True
            )
            raise  # Re-raise with original error details

        except PaymentRequiredError as e:
            self.logger.error(
                "Payment required to access usage statistics",
                extra={
                    'error_type': 'PaymentRequiredError',
                    'code': getattr(e, 'code', None),
                    'details': getattr(e, 'details', {})
                },
                exc_info=True
            )
            raise  # Re-raise with original error details

        except InactiveAccountError as e:
            self.logger.error(
                "Account is inactive, cannot retrieve usage statistics",
                extra={
                    'error_type': 'InactiveAccountError',
                    'code': getattr(e, 'code', None),
                    'details': getattr(e, 'details', {})
                },
                exc_info=True
            )
            raise  # Re-raise with original error details
            
        except Exception as e:
            self.logger.error(
                "Failed to retrieve usage statistics",
                extra={
                    'error_type': type(e).__name__,
                    'code': getattr(e, 'code', None),
                    'details': getattr(e, 'details', {})
                },
                exc_info=True
            )
            raise 