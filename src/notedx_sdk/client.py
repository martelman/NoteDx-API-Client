from typing import Optional, Dict, Any
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

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class NoteDxClient:
    """
    A Pythonic client for the NoteDx API that provides a robust interface for medical note generation.

    This client provides:
    1. Authentication handling:
       - Firebase email/password authentication
       - API key authentication
       - Token refresh management
    2. Environment configuration:
       - Reads configuration from environment variables
       - Supports multiple environments (dev/prod)
    3. Type-safe interfaces:
       - Fully typed methods and responses
       - Literal type constraints for enums
    4. Error handling:
       - Comprehensive exception hierarchy
       - Detailed error messages and context
       - Proper error propagation
    5. Resource management:
       - Audio file upload handling
       - Job status tracking
       - Webhook management

    Environment Variables:
        NOTEDX_EMAIL: Email for authentication
        NOTEDX_PASSWORD: Password for authentication
        NOTEDX_API_KEY: API key for authentication
        NOTEDX_BASE_URL: Base URL for the API (optional)

    Examples:
        Using email/password authentication:
        >>> client = NoteDxClient(
        ...     base_url="https://api.notedx.io/v1",
        ...     email="user@example.com",
        ...     password="password123"
        ... )

        Using API key authentication:
        >>> client = NoteDxClient(
        ...     base_url="https://api.notedx.io/v1",
        ...     api_key="your-api-key"
        ... )

        Using environment variables:
        >>> client = NoteDxClient(base_url="https://api.notedx.io/v1")

    Note:
        - The client uses Firebase Authentication for email/password auth
        - All methods are thread-safe
        - Rate limiting is handled automatically
        - Network errors are properly propagated
    """

    MAX_AUTH_RETRIES = 3  # Maximum number of authentication retry attempts

    def __init__(
        self,
        base_url: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        auto_login: bool = True,
        session: Optional[requests.Session] = None
    ):
        """
        Initialize the NoteDx API client.

        The client can be initialized with either:
        1. Email and password for full account access (using Firebase Auth)
        2. API key for note generation only
        3. No credentials (will read from environment variables)

        Args:
            base_url: Base URL for the API (e.g., "https://api.notedx.io/v1")
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
            - If both email/password and api_key are provided, api_key takes precedence
            - The session parameter allows for custom SSL, proxy, and timeout configuration
            - Auto-login can be disabled if you want to handle authentication manually
        """
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()

        # Environment fallback
        self._email = email or get_env("NOTEDX_EMAIL")
        self._password = password or get_env("NOTEDX_PASSWORD")
        self._api_key = api_key or get_env("NOTEDX_API_KEY")

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
        self.scribe = NoteManager(self)
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
        Call the /auth/login endpoint to authenticate with Firebase.

        Returns:
            Dict containing:
            - user_id: Firebase user ID
            - email: User's email
            - id_token: Firebase ID token (if available)
            - refresh_token: Firebase refresh token (if available)
            - requires_password_change: Whether user needs to change password
            - additional fields as per API response

        Raises:
            AuthenticationError: If credentials are invalid
            NetworkError: If connection fails
            NoteDxError: For other API errors
        """
        if not self._email or not self._password:
            raise AuthenticationError("Missing email/password for login.")
        
        login_url = f"{self.base_url}/auth/login"
        payload = {"email": self._email, "password": self._password}
        
        logger.debug(f"POST {login_url} with payload={payload}")
        resp = self.session.post(login_url, json=payload, timeout=30)
        data = parse_response(resp)

        logger.debug(f"Login response: {data}")
        
        # Store user info
        self._user_id = data.get("user_id")
        if not self._user_id:
            raise AuthenticationError("Login failed: 'user_id' not found in response.")

        # Store Firebase tokens if available
        self._token = data.get("id_token")  # Firebase ID token
        self._refresh_token = data.get("refresh_token")  # Firebase refresh token
        
        # Check if password change is required
        if data.get("requires_password_change"):
            logger.warning("Password change required. Use client.change_password(current_password, new_password) to update your password.")
        
        logger.info(f"Login successful for user: {self._email}")
        return data

    def refresh_token(self) -> Dict[str, Any]:
        """
        Refresh the Firebase ID token using the refresh token.

        Returns:
            Dict containing:
            - id_token: New Firebase ID token
            - refresh_token: New refresh token (if rotated)
            - user_id: Firebase user ID
            - email: User's email

        Raises:
            AuthenticationError: If refresh token is invalid or expired
            NetworkError: If connection fails
            NoteDxError: For other API errors
        """
        if not self._refresh_token:
            raise AuthenticationError("No refresh token available")

        data = self._request("POST", "auth/refresh", data={
            "refresh_token": self._refresh_token
        })

        # Update tokens
        self._token = data.get("id_token")
        if "refresh_token" in data:
            self._refresh_token = data["refresh_token"]

        return data

    def set_token(self, token: str, refresh_token: Optional[str] = None):
        """
        Manually set a token if you already have one (bypasses /auth/login).
        """
        self._token = token
        self._refresh_token = refresh_token

    def set_api_key(self, api_key: str):
        """
        Manually set an API key if you already have one.
        """
        self._api_key = api_key

    def change_password(self, current_password: str, new_password: str) -> Dict[str, Any]:
        """
        Change the user's password and handle re-authentication if required.

        Args:
            current_password: The user's current password
            new_password: The desired new password (must be at least 8 characters)

        Returns:
            Dict containing:
            - message: Success message
            - user_id: Firebase user ID
            - email: User's email
            - requires_reauth: Whether re-authentication is required

        Raises:
            AuthenticationError: If current password is invalid or not logged in
            BadRequestError: If new password doesn't meet requirements
            NoteDxError: For other API errors
        """
        if not self._user_id:
            raise AuthenticationError("Must be logged in to change password")

        if len(new_password) < 8:
            raise BadRequestError("New password must be at least 8 characters long")

        if current_password == new_password:
            raise BadRequestError("New password must be different from current password")

        payload = {
            "current_password": current_password,
            "new_password": new_password
        }

        data = self._request("POST", "auth/change-password", data=payload)
        
        # Check if re-authentication is required
        if data.get("requires_reauth"):
            logger.info("Password changed successfully. Re-authentication required.")
            # Clear tokens to force re-login
            self._token = None
            self._refresh_token = None
            self._user_id = None

        return data

    def _handle_auth_retry(self, endpoint: str, error_msg: str, error_code: str, response_data: Dict[str, Any]) -> bool:
        """
        Handle authentication retry logic for both 401 and 403 errors.
        
        Returns:
            bool: True if should retry, False if max retries exceeded
        """
        # Initialize or increment retry count
        self._auth_retry_counts[endpoint] = self._auth_retry_counts.get(endpoint, 0) + 1
        
        # Check if we've exceeded max retries
        if self._auth_retry_counts[endpoint] > self.MAX_AUTH_RETRIES:
            logger.error(f"Authentication failed after {self.MAX_AUTH_RETRIES} retries for endpoint: {endpoint}")
            self._auth_retry_counts[endpoint] = 0  # Reset for next time
            raise AuthenticationError(f"Authorization failed after {self.MAX_AUTH_RETRIES} retries", error_code, response_data)
            
        # Try to refresh token first
        if self._refresh_token:
            try:
                logger.info("Authorization failed, attempting token refresh...")
                self.refresh_token()
                return True
            except Exception as e:
                logger.debug(f"Token refresh failed, falling back to re-login: {str(e)}")
                if self._email and self._password:
                    logger.info("Token refresh failed, attempting re-login...")
                    self.login()
                    return True
        elif self._email and self._password:
            logger.info("No refresh token available, attempting re-login...")
            self.login()
            return True
            
        return False

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Any = None,
        params: Dict[str, Any] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Internal method to perform an HTTP request and parse the response.

        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint
            data (Any, optional): Request data
            params (Dict[str, Any], optional): Query parameters
            timeout (int, optional): Request timeout in seconds. Defaults to 60.

        Returns:
            Dict[str, Any]: Parsed response data

        Raises:
            NetworkError: For connection/timeout issues
            AuthenticationError: For authentication failures
            AuthorizationError: For permission issues
            PaymentRequiredError: For payment required errors
            InactiveAccountError: For inactive account errors
            BadRequestError: For invalid request errors
            NotFoundError: For 404 errors
            RateLimitError: For rate limit errors
            InternalServerError: For server errors
        """
        url = f"{self.base_url}/{endpoint.strip('/')}"
        
        # For endpoints that don't require authentication, skip token
        no_auth_endpoints = {"auth/login", "auth/refresh"}
        
        if endpoint in no_auth_endpoints:
            headers = {}
        else:
            # Check if we're switching HTTP methods on the same endpoint
            last_method = self._last_successful_methods.get(endpoint)
            if last_method and last_method != method:
                logger.debug(f"HTTP method changed for endpoint {endpoint} ({last_method} -> {method}). Attempting token refresh.")
                if self._refresh_token:
                    try:
                        self.refresh_token()
                    except Exception as e:
                        logger.debug(f"Token refresh failed, falling back to re-login: {str(e)}")
                        if self._email and self._password:
                            self.login()
                elif self._email and self._password:
                    self.login()
            
            # For authenticated endpoints, ensure we have a valid token
            if not self._token and self._email and self._password:
                logger.debug("No token available. Attempting login before request.")
                self.login()
            
            # Now check if we have authentication
            if not self._token and not self._api_key:
                raise AuthenticationError("No valid authentication token or API key available")
            
            # Build headers with token or API key
            headers = build_headers(token=self._token, api_key=self._api_key)
            logger.debug(f"Using headers: {headers}")

        logger.debug(f"{method} {url}, params={params}, data={data}")

        try:
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

            # If request is successful, update the last successful method and reset retry counter
            if 200 <= response.status_code < 300:
                self._last_successful_methods[endpoint] = method
                self._auth_retry_counts[endpoint] = 0

            # Handle rate limiting
            if response.status_code == 429:
                reset_time = response.headers.get('X-RateLimit-Reset')
                raise RateLimitError(
                    "API rate limit exceeded",
                    reset_time=reset_time,
                    details={"headers": dict(response.headers)}
                )

            # Handle various error responses
            if response.status_code >= 400:
                # Handle different error message formats
                error_msg = (
                    response_data.get("message") or  # Standard format
                    response_data.get("Message") or  # AWS API Gateway format
                    response_data.get("error", {}).get("message") or 
                    str(response_data) or 
                    "Unknown error"
                )
                error_code = response_data.get("error", {}).get("code")
                
                if response.status_code == 401:
                    # Handle Firebase auth errors
                    if "Invalid API Key" in error_msg:
                        raise AuthenticationError(error_msg, error_code, response_data)
                    elif "User not found" in error_msg:
                        raise AuthenticationError(error_msg, "USER_NOT_FOUND", response_data)
                    elif "Invalid credentials" in error_msg:
                        raise AuthenticationError(error_msg, "INVALID_CREDENTIALS", response_data)
                    elif "Token expired" in error_msg or "expired" in error_msg.lower():
                        # Try to refresh token and retry request once
                        if endpoint != "auth/refresh":  # Prevent infinite recursion
                            logger.info("Token expired, attempting refresh...")
                            if self._handle_auth_retry(endpoint, error_msg, error_code, response_data):
                                return self._request(method, endpoint, data, params, timeout)
                        raise AuthenticationError(error_msg, "TOKEN_EXPIRED", response_data)
                    else:
                        # Try to refresh token first, then fall back to re-login
                        if endpoint != "auth/refresh" and self._handle_auth_retry(endpoint, error_msg, error_code, response_data):
                            return self._request(method, endpoint, data, params, timeout)
                        raise AuthenticationError(error_msg, error_code, response_data)

                elif response.status_code == 402:
                    raise PaymentRequiredError(error_msg, error_code, response_data)
                
                elif response.status_code == 403:
                    if "Account Inactive" in error_msg:
                        raise InactiveAccountError(error_msg, error_code, response_data)
                    elif "Token revoked" in error_msg or "not authorized" in error_msg.lower():
                        # Try to refresh token first, then fall back to re-login
                        if self._handle_auth_retry(endpoint, error_msg, error_code, response_data):
                            return self._request(method, endpoint, data, params, timeout)
                        raise AuthorizationError(error_msg, error_code, response_data)
                    # For any other 403, try refresh first, then re-login
                    if self._handle_auth_retry(endpoint, error_msg, error_code, response_data):
                        return self._request(method, endpoint, data, params, timeout)
                    raise AuthorizationError(error_msg, error_code, response_data)
                
                elif response.status_code == 404:
                    raise NotFoundError(error_msg, error_code, response_data)
                
                elif response.status_code == 400:
                    raise BadRequestError(error_msg, error_code, response_data)
                
                elif response.status_code >= 500:
                    raise InternalServerError(error_msg, error_code, response_data)
                
                else:
                    raise NoteDxError(error_msg, error_code, response_data)

            return response_data

        except requests.Timeout:
            raise NetworkError(
                f"Request timed out after {timeout} seconds",
                "TIMEOUT",
                {"url": url, "method": method}
            )
        
        except requests.ConnectionError as e:
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
                    raise InternalServerError(str(e))
                else:
                    raise BadRequestError(str(e))
            raise NetworkError(f"Request failed: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error in _request: {str(e)}")
            raise