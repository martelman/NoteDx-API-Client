from typing import Optional, Dict, Any, Union
import requests
import logging

from .account.account_manager import AccountManager
from .api_keys.key_manager import KeyManager
from .webhooks.webhook_manager import WebhookManager
from .core.note_manager import NoteManager
from .usage.usage_manager import UsageManager
from .helpers import (
    get_env,
    parse_response,
    build_headers
)
from .exceptions import (
    ConflictError,
    InvalidFieldError,
    NoteDxError,
    AuthenticationError,
    AuthorizationError,
    PaymentRequiredError,
    InactiveAccountError,
    NotFoundError,
    BadRequestError,
    RateLimitError,
    NetworkError,
    InternalServerError,
)

# Initialize SDK logger
logger = logging.getLogger("notedx_sdk")
logger.addHandler(logging.NullHandler())  # Default to no handler
logger.setLevel(logging.INFO)  # Default to INFO level

class NoteDxClient:
    """
    A Pythonic client for the NoteDx API that provides a robust interface for medical note generation.
    
    This client wraps the NoteDx API endpoints, providing comprehensive functionality for medical
    note generation and account management. It handles authentication, environment configuration,
    and resource management with robust error handling.
    
    Features:
        - Account creation and management
        - Authentication handling (Firebase email/password and API key)
        - Environment configuration
        - Type-safe interfaces
        - Comprehensive error handling
        - Resource management
    
    Parameters:
        email (str, optional): Email for authentication. If not provided, reads from NOTEDX_EMAIL env var.
        password (str, optional): Password for authentication. If not provided, reads from NOTEDX_PASSWORD env var.
        api_key (str, optional): API key for authentication. If not provided, reads from NOTEDX_API_KEY env var.
        auto_login (bool, optional): If True, automatically logs in when credentials are provided. Defaults to True.
        session (requests.Session, optional): Custom requests.Session for advanced configuration.
    
    Raises:
        ValidationError: If the base_url is invalid
        AuthenticationError: If credentials are invalid or missing
        NetworkError: If unable to connect to the API
        InternalServerError: If server error occurs during initialization
    
    Example:
        ```python
        # Create a new account
        result = NoteDxClient.account.create_account(
            email="user@example.com",
            password="secure-password",
            company_name="Medical Center Inc."
        )
        print(f"Sandbox API Key: {result['sandbox_api_key']}")
        
        # Using email/password authentication
        client = NoteDxClient(
            email="user@example.com",
            password="password123"
        )
        # Client automatically logs in
        print(client.account.get_account())
        
        # Using API key authentication
        client = NoteDxClient(api_key="your-api-key")
        # Process an audio file
        response = client.notes.process_audio(
            file_path="recording.mp3",
            template="primaryCare"
        )
        ```
    
    Notes:
        - The session parameter allows for custom SSL, proxy, and timeout configuration
        - Auto-login can be disabled if you want to handle authentication manually
        - Each account starts with 100 free jobs (live API key)
        - Sandbox API keys have unlimited usage for testing
    """

    MAX_AUTH_RETRIES = 3
    BASE_URL = "https://api.notedx.io/v1"

    @classmethod
    def configure_logging(cls, level: int = logging.INFO, handler: Optional[logging.Handler] = None,
                        format_string: Optional[str] = None) -> None:
        """
        Configure logging for the NoteDx SDK.

        This method allows customization of logging behavior, including log level,
        custom handlers, and format strings.

        Args:
            level (int, optional): The logging level (e.g., logging.DEBUG, logging.INFO).
                Defaults to logging.INFO.
            handler (logging.Handler, optional): Custom logging handler. If None, logs to console.
            format_string (str, optional): Custom format string for log messages.
                Defaults to '%(asctime)s - %(name)s - %(levelname)s - %(message)s'.

        Example:
            ```python
            Enable debug logging to console:
            >>> NoteDxClient.configure_logging(logging.DEBUG)

            Log to a file with custom format:
            >>> file_handler = logging.FileHandler('notedx.log')
            >>> NoteDxClient.configure_logging(
            ...     level=logging.INFO,
            ...     handler=file_handler,
            ...     format_string='%(asctime)s - %(message)s'
            ... )
            ```
        """
        global logger
        
        # Remove existing handlers
        logger.handlers.clear()
        
        # Set log level
        logger.setLevel(level)
        
        # Create handler if none provided
        if handler is None:
            handler = logging.StreamHandler()
        
        # Create formatter
        if format_string is None:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(format_string)
        handler.setFormatter(formatter)
        
        # Add handler
        logger.addHandler(handler)
        
        logger.debug("Logging configured with level %s", logging.getLevelName(level))

    @classmethod
    def set_log_level(cls, level: int) -> None:
        """
        Set the logging level for the NoteDx SDK.

        A convenience method to quickly change just the log level without
        reconfiguring the entire logging setup.

        Args:
            level (int): The logging level to set (e.g., logging.DEBUG, logging.INFO).

        Example:
            ```python
            >>> NoteDxClient.set_log_level(logging.DEBUG)  # Enable debug logging
            >>> NoteDxClient.set_log_level(logging.WARNING)  # Only log warnings and errors
            ```
        """
        logger.setLevel(level)
        logger.debug("Log level set to %s", logging.getLevelName(level))

    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        auto_login: bool = True,
        session: Optional[requests.Session] = None
    ):
        """
        Initialize the NoteDx API client.

        The client can be initialized with:

        1. Email and password for account access (using Firebase Auth)
        2. API key for note generation only
        3. Both email/password and API key for full account access and note generation
        3. No credentials (will read from environment variables)

        Args:
            email: Email for authentication. If not provided, reads from NOTEDX_EMAIL env var
            password: Password for authentication. If not provided, reads from NOTEDX_PASSWORD env var
            api_key: API key for authentication. If not provided, reads from NOTEDX_API_KEY env var
            auto_login: If True, automatically logs in when credentials are provided
            session: Optional custom requests.Session for advanced configuration

        Raises:
            ValidationError: If the base_url is invalid
            AuthenticationError: If credentials are invalid or missing
            NetworkError: If unable to connect to the API
            InternalServerError: If server error occurs during initialization

        Note:
            - The session parameter allows for custom SSL, proxy, and timeout configuration
            - Auto-login can be disabled if you want to handle authentication manually
        """
        self.base_url = self.BASE_URL
        self.session = session or requests.Session()

        # Environment fallback
        self._email = email or get_env("NOTEDX_EMAIL") or None
        self._password = password or get_env("NOTEDX_PASSWORD") or None
        self._api_key = api_key or get_env("NOTEDX_API_KEY") or None

        # Validate that we have some form of authentication
        if not any([self._email and self._password, self._api_key]):
            raise AuthenticationError("No authentication credentials provided. Please provide either an API key or email/password combination.")

        # Firebase auth state
        self._user_id: Optional[str] = None
        self._token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        
        # Track last successful request method for each endpoint
        self._last_successful_methods: Dict[str, str] = {}

        # Track auth retry attempts per endpoint
        self._auth_retry_counts: Dict[str, int] = {}

        # Initialize managers
        self.account = AccountManager(self)
        self.keys = KeyManager(self)
        self.webhooks = WebhookManager(self)
        self.notes = NoteManager(self)
        self.usage = UsageManager(self)

        logger.debug(f"Email: {self._email}, Password: {self._password}, API Key: {self._api_key}")
        # Attempt login if we have email/password credentials
        if auto_login and self._email and self._password:
            logger.debug("Auto-login is enabled and email/password provided. Attempting login.")
            self._maybe_login()

    # --------------------------------------------------
    # Internal Auth & Request Handling
    # --------------------------------------------------
    def _maybe_login(self) -> None:
        """
        If we don't have a token and we have credentials, call /auth/login automatically.
        """
        if self._token:
            return  # Already have token
        if not self._email or not self._password:
            logger.info("No email/password credentials found. Skipping auto-login.")
            return
        logger.info(f"Attempting auto-login with user: {self._email}")
        self.login()

    def login(self) -> Dict[str, Any]:
        """
        Authenticate with the NoteDx API using Firebase email/password authentication.

        ```bash
        POST /auth/login
        ```

        This method wraps the /auth/login endpoint, handling Firebase authentication
        and token management. On successful login, it stores the authentication tokens
        for subsequent requests.

        Returns:
            dict: Authentication response containing:

                - user_id (str): Firebase user ID
                - email (str): User's email address
                - id_token (str): Firebase ID token for API requests
                - refresh_token (str): Token for refreshing authentication


        Raises:
            AuthenticationError: If credentials are invalid or missing
            NetworkError: If connection fails or request times out
            NoteDxError: For other API errors
        """
        if not self._email or not self._password:
            logger.error("Missing email/password for login")
            raise AuthenticationError("Missing email/password for login.")
        
        login_url = f"{self.base_url}/auth/login"
        payload = {"email": self._email, "password": self._password}
        
        # Redact password in logs
        log_payload = {"email": self._email, "password": "***"}
        logger.debug("Initiating login request to %s", login_url)
        logger.debug("Login payload: %s", log_payload)
        
        try:
            resp = self.session.post(login_url, json=payload, timeout=30)
            data = parse_response(resp)

            # Log response with sensitive data redacted
            log_data = {**data}
            if "id_token" in log_data:
                log_data["id_token"] = "***"
            if "refresh_token" in log_data:
                log_data["refresh_token"] = "***"
            logger.debug("Login response received: %s", log_data)
            
            # Store user info
            self._user_id = data.get("user_id")
            if not self._user_id:
                logger.error("Login failed: 'user_id' not found in response")
                raise AuthenticationError("Login failed: 'user_id' not found in response.")

            # Store Firebase tokens if available
            self._token = data.get("id_token")  # Firebase ID token
            self._refresh_token = data.get("refresh_token")  # Firebase refresh token

            # Validate required tokens
            if not self._token or not self._refresh_token:
                logger.error("Login failed: Missing required tokens in response")
                raise AuthenticationError("Missing required tokens in response")
            
            logger.info("Successfully logged in as: %s", self._email)
            return data

        except requests.Timeout:
            logger.error("Login request timed out after 30 seconds")
            raise NetworkError("Login request timed out")
            
        except requests.ConnectionError as e:
            logger.error("Connection error during login: %s", str(e))
            raise NetworkError(f"Connection error during login: {str(e)}")
            
        except Exception as e:
            logger.error("Login failed: %s", str(e))
            raise

    def refresh_token(self) -> Dict[str, Any]:
        """
        Refresh the Firebase authentication token using the current refresh token.

        ```bash
        POST /auth/refresh
        ```

        This method wraps the /auth/refresh endpoint, handling token refresh and rotation.
        It automatically updates the stored tokens on successful refresh.

        Returns:
            dict: Refresh response containing:

                - id_token (str): New Firebase ID token
                - refresh_token (str): New refresh token (if rotated)
                - user_id (str): Firebase user ID
                - email (str): User's email

        Raises:
            AuthenticationError: If refresh token is invalid, expired, or missing
            NetworkError: If connection fails
            NoteDxError: For other API errors

        Example:
            ```python
            >>> # Refresh token when needed
            >>> try:
            ...     new_tokens = client.refresh_token()
            ... except AuthenticationError:
            ...     # Handle token refresh failure
            ...     client.login()
            ```
        """
        if not self._refresh_token:
            logger.error("Cannot refresh token: no refresh token available")
            raise AuthenticationError("No refresh token available")

        try:
            logger.debug("Initiating token refresh")
            data = self._request("POST", "auth/refresh", data={
                "refresh_token": self._refresh_token
            })

            # Log response with sensitive data redacted
            log_data = {**data}
            if "id_token" in log_data:
                log_data["id_token"] = "***"
            if "refresh_token" in log_data:
                log_data["refresh_token"] = "***"
            logger.debug("Token refresh response: %s", log_data)

            # Update tokens
            self._token = data.get("id_token")
            if not self._token:
                logger.error("Token refresh failed: no id_token in response")
                raise AuthenticationError("Token refresh failed: no id_token in response")

            # Update refresh token if rotated
            if "refresh_token" in data:
                self._refresh_token = data["refresh_token"]
                logger.debug("Refresh token was rotated")

            logger.info("Successfully refreshed authentication token")
            return data

        except AuthenticationError:
            # Clear tokens on authentication failure
            logger.warning("Token refresh failed, clearing stored tokens")
            self._token = None
            self._refresh_token = None
            raise

    def set_token(self, token: str, refresh_token: Optional[str] = None) -> None:
        """
        Manually set authentication tokens for the client.

        This method allows direct setting of authentication tokens, bypassing the
        normal login flow. Useful when you already have valid Firebase tokens from
        another source.

        Args:
            token (str): Firebase ID token for API authentication
            refresh_token (str, optional): Firebase refresh token for token renewal

        Example:
            ```python
            >>> # Using tokens from another source
            >>> client = NoteDxClient()
            >>> client.set_token(
            ...     token="firebase_id_token",
            ...     refresh_token="firebase_refresh_token"
            ... )
            >>> # Now you can make authenticated requests
            >>> account_info = client.account.get_account()
            ```

        Note:
            - The tokens must be valid Firebase tokens
            - Without a refresh_token, you won't be able to automatically refresh authentication
            - Invalid tokens will cause AuthenticationError on API requests
        """
        logger.debug("Setting manual authentication tokens")
        self._token = token
        self._refresh_token = refresh_token
        logger.info("Authentication tokens set manually")

    def set_api_key(self, api_key: str) -> None:
        """
        Manually set an API key for the client.

        This method allows direct setting of an API key for authentication.
        API keys provide limited access focused on note generation endpoints.

        Args:
            api_key (str): NoteDx API key for authentication

        Example:
            ```python
            >>> client = NoteDxClient()
            >>> client.set_api_key("your_api_key")
            >>> # Now you can use note generation endpoints
            >>> response = client.notes.process_audio(
            ...     file_path="recording.mp3",
            ...     template="primaryCare"
            ... )
            ```

        Note:
            - API keys only provide access to note generation endpoints
            - For full account access, use email/password authentication
            - Invalid API keys will cause AuthenticationError on API requests
        """
        logger.debug("Setting manual API key")
        self._api_key = api_key
        logger.info("API key set manually")

    def change_password(self, current_password: str, new_password: str) -> Dict[str, Any]:
        """
        Change the password for the currently logged in user.

        ```bash
        POST /auth/change-password
        ```

        This method wraps the /auth/change-password endpoint, handling password updates
        and token management. On successful password change, it may require re-authentication.

        Args:
            current_password (str): Current password for verification
            new_password (str): New password to set

        Returns:
            dict: Response data containing:
            
                - success (bool): Whether password was changed
                - requires_reauth (bool): Whether re-authentication is required

        Raises:
            AuthenticationError: If not logged in or current password is incorrect
            BadRequestError: If new password doesn't meet requirements
            NetworkError: If connection fails or request times out
            NoteDxError: For other API errors

        Example:
            ```python
            >>> client = NoteDxClient(email="user@example.com", password="old-pass")
            >>> result = client.change_password("old-pass", "new-pass")
            >>> if result["requires_reauth"]:
            ...     client.login()  # Re-authenticate with new password
            ```
        """
        if not self._user_id:
            logger.error("Cannot change password: user not logged in")
            raise AuthenticationError("Must be logged in to change password")

        # Validate password requirements
        if len(new_password) < 8:
            logger.error("Password change rejected: new password too short")
            raise BadRequestError("New password must be at least 8 characters long")

        if current_password == new_password:
            logger.error("Password change rejected: new password same as current")
            raise BadRequestError("New password must be different from current password")

        try:
            logger.debug("Initiating password change for user %s", self._email)
            payload = {
                "current_password": current_password,
                "new_password": new_password
            }

            # Log with redacted passwords
            log_payload = {
                "current_password": "***",
                "new_password": "***"
            }
            logger.debug("Password change request: %s", log_payload)

            data = self._request("POST", "auth/change-password", data=payload)
            
            # Check if re-authentication is required
            if data.get("requires_reauth"):
                logger.info("Password changed successfully. Re-authentication required")
                # Clear tokens to force re-login
                self._token = None
                self._refresh_token = None
                self._user_id = None
            else:
                logger.info("Password changed successfully")

            return data

        except AuthenticationError as e:
            if "Current password is incorrect" in str(e):
                logger.error("Password change failed: invalid current password")
                raise AuthenticationError("Current password is incorrect")
            raise

        except Exception as e:
            logger.error("Password change failed: %s", str(e))
            raise

    def _handle_auth_retry(self, endpoint: str, error_msg: str, error_code: str, response_data: Dict[str, Any]) -> bool:
        """
        Handle authentication retry logic for failed API requests.

        This internal method implements a retry strategy for authentication failures,
        attempting token refresh and re-login as appropriate. It tracks retry attempts
        per endpoint to prevent infinite loops.

        Args:
            endpoint (str): The API endpoint that failed
            error_msg (str): Error message from the failed request
            error_code (str): Error code from the API response
            response_data (dict): Complete error response data

        Returns:
            bool: True if the request should be retried, False if max retries exceeded

        Raises:
            AuthenticationError: If authentication fails after max retries

        Note:
            - Implements exponential backoff for retries
            - Tries token refresh before falling back to re-login
            - Tracks retries per endpoint separately
        """
        # Initialize or increment retry count
        self._auth_retry_counts[endpoint] = self._auth_retry_counts.get(endpoint, 0) + 1
        retry_count = self._auth_retry_counts[endpoint]
        
        logger.debug(
            "Handling authentication retry for endpoint %s (attempt %d/%d)",
            endpoint, retry_count, self.MAX_AUTH_RETRIES
        )
        
        # Check if we've exceeded max retries
        if retry_count > self.MAX_AUTH_RETRIES:
            logger.error(
                "Authentication failed after %d retries for endpoint: %s",
                self.MAX_AUTH_RETRIES, endpoint
            )
            self._auth_retry_counts[endpoint] = 0  # Reset for next time
            raise AuthenticationError(
                f"Authorization failed after {self.MAX_AUTH_RETRIES} retries",
                error_code,
                response_data
            )
            
        # Try to refresh token first
        if self._refresh_token:
            try:
                logger.info(
                    "Authorization failed for endpoint %s, attempting token refresh (attempt %d/%d)",
                    endpoint, retry_count, self.MAX_AUTH_RETRIES
                )
                self.refresh_token()
                return True
            except Exception as e:
                logger.debug(
                    "Token refresh failed for endpoint %s, falling back to re-login: %s",
                    endpoint, str(e)
                )
                if self._email and self._password:
                    logger.info(
                        "Token refresh failed for endpoint %s, attempting re-login (attempt %d/%d)",
                        endpoint, retry_count, self.MAX_AUTH_RETRIES
                    )
                    self.login()
                    return True
        elif self._email and self._password:
            logger.info(
                "No refresh token available for endpoint %s, attempting re-login (attempt %d/%d)",
                endpoint, retry_count, self.MAX_AUTH_RETRIES
            )
            self.login()
            return True
            
        logger.warning(
            "No authentication retry options available for endpoint %s after %d attempts",
            endpoint, retry_count
        )
        return False

    @classmethod
    def _create_account_request(
        cls,
        method: str,
        endpoint: str,
        data: Any = None,
        params: Dict[str, Any] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """Internal method for making unauthenticated requests during account creation"""
        base_url = get_env("NOTEDX_API_URL", "https://api.notedx.io/v1")
        url = f"{base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers={},
                json=data,
                params=params,
                timeout=timeout
            )

            try:
                response_data = response.json()
            except ValueError:
                response_data = {"message": response.text}

            if 200 <= response.status_code < 300:
                return response_data

            error_msg = (
                response_data.get("message") or
                response_data.get("error", {}).get("message") or
                str(response_data)
            )
            error_code = response_data.get("error", {}).get("code")
            error_details = response_data.get("details", {})

            if response.status_code == 400:
                raise BadRequestError(error_msg, error_code, error_details)
            elif response.status_code == 409:
                raise ConflictError(error_msg, error_code, error_details)
            else:
                raise NoteDxError(error_msg, error_code, error_details)

        except requests.Timeout:
            raise NetworkError(f"Request timed out after {timeout} seconds")
        except requests.ConnectionError as e:
            raise NetworkError(f"Connection error: {str(e)}")
        except Exception as e:
            if not isinstance(e, NoteDxError):
                raise NetworkError(f"Request failed: {str(e)}")
            raise

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Any = None,
        params: Dict[str, Any] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the NoteDx API.

        Args:
            method: HTTP method (GET, POST, etc)
            endpoint: API endpoint path
            data: Request body data
            params: URL parameters
            timeout: Request timeout in seconds

        Returns:
            API response data as dictionary

        Raises:
            Various NoteDxError subclasses based on response
        """
        if not endpoint:
            raise ValueError("Endpoint is required")

        # Construct URL
        base_url = get_env("NOTEDX_API_URL", "https://api.notedx.io/v1")
        url = f"{base_url}/{endpoint.lstrip('/')}"

        no_auth_endpoints = {"auth/login", "auth/refresh", "auth/create-account"}
        
        if endpoint in no_auth_endpoints:
            headers = {}
            logger.debug("Making unauthenticated request to %s", endpoint)
        else:
            last_method = self._last_successful_methods.get(endpoint)
            if last_method and last_method != method:
                logger.debug(
                    "HTTP method changed for endpoint %s (%s -> %s). Attempting token refresh",
                    endpoint, last_method, method
                )
                if self._refresh_token:
                    try:
                        self.refresh_token()
                    except Exception as e:
                        logger.debug(
                            "Token refresh failed after method change, falling back to re-login: %s",
                            str(e)
                        )
                        if self._email and self._password:
                            self.login()
                elif self._email and self._password:
                    self.login()

            if not self._token and self._email and self._password:
                logger.debug("No token available for %s. Attempting login", endpoint)
                self.login()

            if not self._token and not self._api_key:
                logger.error("No valid authentication available for %s", endpoint)
                raise AuthenticationError("No valid authentication token or API key available")

            headers = build_headers(token=self._token, api_key=self._api_key)

            log_headers = {k: '***' if k in ['Authorization', 'X-Api-Key'] else v 
                         for k, v in headers.items()}
            logger.debug("Using headers: %s", log_headers)

        try:
            log_data = {
                'method': method,
                'url': url,
                'params': params
            }
            if data:
                log_data['data'] = self._redact_sensitive_data(data)
            logger.debug("Making request: %s", log_data)

            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=timeout
            )

            try:
                response_data = response.json()
            except ValueError:
                response_data = {"message": response.text}

            # Log response details with sensitive data redacted
            log_response = {
                'status_code': response.status_code,
                'data': self._redact_sensitive_data(response_data)
            }
            logger.debug("Received response: %s", log_response)

            # If request is successful, update the last successful method
            if 200 <= response.status_code < 300:
                self._last_successful_methods[endpoint] = method
                self._auth_retry_counts[endpoint] = 0
                
                # For login endpoint, log success
                if endpoint == "auth/login":
                    logger.info("Successfully logged in as: %s", self._email)
                    
                return response_data

            # Handle rate limiting
            if response.status_code == 429:
                reset_time = response.headers.get('X-RateLimit-Reset')
                logger.warning(
                    "Rate limit exceeded for %s. Reset at: %s",
                    endpoint, reset_time
                )
                raise RateLimitError(
                    "API rate limit exceeded",
                    reset_time=reset_time,
                    details={"headers": dict(response.headers)}
                )

            # Handle various error responses
            error_msg = (
                response_data.get("message") or
                response_data.get("Message") or
                response_data.get("error", {}).get("message") or
                str(response_data) or
                "Unknown error"
            )
            error_code = response_data.get("error", {}).get("code")
            error_details = response_data.get("details", {})
            
            if response.status_code == 401:
                # Handle Firebase auth errors
                if "Invalid API Key" in error_msg:
                    logger.error("Invalid API key used for %s", endpoint)
                    raise AuthenticationError(error_msg, error_code, error_details)
                elif "User not found" in error_msg:
                    logger.error("User not found for %s", endpoint)
                    raise AuthenticationError(error_msg, "USER_NOT_FOUND", error_details)
                elif "Invalid credentials" in error_msg:
                    logger.error("Invalid credentials for %s", endpoint)
                    raise AuthenticationError(error_msg, "INVALID_CREDENTIALS", error_details)
                elif "Token expired" in error_msg or "expired" in error_msg.lower():
                    logger.info("Token expired for %s, attempting refresh", endpoint)
                    # Try to refresh token and retry request once
                    if endpoint != "auth/refresh":  # Prevent infinite recursion
                        if self._handle_auth_retry(endpoint, error_msg, error_code, response_data):
                            return self._request(method, endpoint, data, params, timeout)
                    raise AuthenticationError(error_msg, "TOKEN_EXPIRED", error_details)
                else:
                    # Try to refresh token first, then fall back to re-login
                    if endpoint != "auth/refresh" and self._handle_auth_retry(endpoint, error_msg, error_code, response_data):
                        return self._request(method, endpoint, data, params, timeout)
                    raise AuthenticationError(error_msg, error_code, error_details)

            elif response.status_code == 402:
                logger.error("Payment required for %s: %s", endpoint, error_msg)
                raise PaymentRequiredError(error_msg, error_code, error_details)
            
            elif response.status_code == 403:
                if "Account Inactive" in error_msg:
                    logger.error("Inactive account accessing %s", endpoint)
                    raise InactiveAccountError(error_msg, error_code, error_details)
                elif "Token revoked" in error_msg or "not authorized" in error_msg.lower():
                    logger.info("Token revoked or unauthorized for %s, attempting refresh", endpoint)
                    # Try to refresh token first, then fall back to re-login
                    if self._handle_auth_retry(endpoint, error_msg, error_code, response_data):
                        return self._request(method, endpoint, data, params, timeout)
                    raise AuthorizationError(error_msg, error_code, error_details)
                # For any other 403, try refresh first, then re-login
                if self._handle_auth_retry(endpoint, error_msg, error_code, response_data):
                    return self._request(method, endpoint, data, params, timeout)
                raise AuthorizationError(error_msg, error_code, error_details)

            elif response.status_code == 404:
                logger.error("Resource not found at %s", endpoint)
                raise NotFoundError(error_msg, error_code, error_details)
            
            elif response.status_code == 400:
                logger.error("Bad request to %s: %s", endpoint, error_msg)
                raise BadRequestError(error_msg, error_code, error_details)
            
            elif response.status_code == 409:
                logger.error("Conflict error from %s: %s", endpoint, error_msg)
                raise ConflictError(error_msg, error_code, error_details)
            
            elif response.status_code >= 500:
                logger.error("Server error from %s: %s", endpoint, error_msg)
                raise InternalServerError(error_msg, error_code, error_details)
            
            else:
                logger.error(
                    "Unexpected status code %d from %s: %s",
                    response.status_code, endpoint, error_msg
                )
                raise NoteDxError(error_msg, error_code, error_details)

        except requests.Timeout:
            logger.error("Request to %s timed out after %d seconds", endpoint, timeout)
            raise NetworkError(
                f"Request timed out after {timeout} seconds",
                "TIMEOUT",
                {"url": url, "method": method}
            )
        
        except requests.ConnectionError as e:
            logger.error("Connection error for %s: %s", endpoint, str(e))
            raise NetworkError(
                f"Connection error: {str(e)}",
                "CONNECTION_ERROR",
                {"url": url, "method": method}
            )

        except requests.RequestException as e:
            if isinstance(e, requests.HTTPError) and e.response is not None:
                # Handle any missed HTTP errors
                status_code = e.response.status_code
                if status_code >= 500:
                    logger.error("Server error from %s: %s", endpoint, str(e))
                    raise InternalServerError(str(e))
                else:
                    logger.error("HTTP error from %s: %s", endpoint, str(e))
                    raise BadRequestError(str(e))
            logger.error("Request to %s failed: %s", endpoint, str(e))
            raise NetworkError(f"Request failed: {str(e)}")
        
        except Exception as e:
            logger.error("Unexpected error in request to %s: %s", endpoint, str(e))
            raise

    @staticmethod
    def _redact_sensitive_data(data: Any) -> Any:
        """Redact sensitive information from data for logging purposes.

        Parameters:
            data: Data to redact (dict, list, or scalar value)

        Returns:
            Redacted copy of the data with sensitive information masked
        """
        if isinstance(data, dict):
            return {
                k: '***' if k.lower() in {
                    'password', 'token', 'key', 'secret', 'authorization',
                    'refresh_token', 'id_token', 'api_key'
                } else NoteDxClient._redact_sensitive_data(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [NoteDxClient._redact_sensitive_data(item) for item in data]
        return data

    @classmethod
    def create_account(
        cls,
        email: str,
        password: str,
        company_name: str,
        contact_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new NoteDx account.

        ```bash
        POST /auth/create-account
        ```

        This operation:

        1. Creates a new user account
        2. Generates sandbox and live API keys
        3. Sends email verification link
        4. Sets up initial account settings

        Args:
            email: Email address for the account
            password: Account password (must be at least 8 characters)
            company_name: Company or organization name
            contact_phone: Optional contact phone number

        Returns:
            Dict containing:

            - message: Success message from the API
            - user_id: Created account identifier
            - sandbox_api_key: API key for testing (unlimited usage)
            - live_api_key: API key for production (includes free trial)
            - requires_verification: True (email verification required)
            - next_steps: List of steps to complete setup

        Raises:
            BadRequestError: If required fields are missing or invalid
            InvalidFieldError: If email format is invalid
            ConflictError: If email is already registered
            NetworkError: If connection issues occur
        """
        logger.debug("Preparing account creation request")

        # Validate password length
        if len(password) < 8:
            logger.error("Password validation failed: too short")
            raise InvalidFieldError(
                "password",
                "INVALID_PASSWORD_LENGTH",
                {"min_length": 8}
            )

        # Prepare request data
        create_data = {
            "email": email.strip(),
            "password": password.strip(),
            "company_name": company_name.strip()
        }

        # Add optional phone if provided
        if contact_phone:
            create_data["contact_phone"] = contact_phone.strip()

        try:
            response = cls._create_account_request(
                "POST",
                "auth/create-account",
                data=create_data
            )

            # Log success with important next steps
            sandbox_key = response.get('sandbox_api_key')
            live_key = response.get('live_api_key')
            
            logger.warning(
                "Account created successfully! Important next steps:\n"
                "1. Check your email (%s) for the verification link\n"
                "2. Click the verification link to activate your account\n"
                "3. List your API keys, update them and or save them:\n"
                "   - Sandbox API Key (unlimited testing): %s\n"
                "   - Live API Key (includes free trial and LLM endpoints): %s",
                email,
                sandbox_key[:8] + '...' if sandbox_key else 'Not generated',
                live_key[:8] + '...' if live_key else 'Not generated'
            )

            # Create a client instance and set the API key
            client = cls(email=email, password=password, auto_login=False)
            if live_key:
                client.set_api_key(live_key)
            
            # Log additional details at debug level
            log_data = {
                'email': email,
                'company': company_name,
                'user_id': response.get('user_id'),
                'requires_verification': response.get('requires_verification', True),
                'next_steps': response.get('next_steps', []),
                'has_sandbox_key': bool(sandbox_key),
                'has_live_key': bool(live_key)
            }
            logger.debug("Account creation details", extra=log_data)

            return response

        except Exception as e:
            # Log error (without sensitive data)
            logger.error(
                "Failed to create account",
                extra={
                    'error_type': type(e).__name__,
                    'code': getattr(e, 'code', None),
                    'details': getattr(e, 'details', {}),
                    'email': email
                },
                exc_info=True
            )
            raise