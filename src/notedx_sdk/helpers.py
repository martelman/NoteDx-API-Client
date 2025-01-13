import os
import logging
import requests
from typing import Dict, Any
from .exceptions import (
    NoteDxError,
    AuthenticationError,
    BadRequestError,
    PaymentRequiredError,
    InactiveAccountError,
    NotFoundError,
    InternalServerError
)

logger = logging.getLogger(__name__)


def get_env(key: str, default: str = "") -> str:
    """Get an environment variable or return a default value.

    Parameters:
        key: The environment variable name to fetch
        default: The default value to return if not found

    Returns:
        The environment variable value or the default
    """
    return os.environ.get(key, default)


def parse_response(response: requests.Response) -> Dict[str, Any]:
    """Parse an HTTP response and handle errors appropriately.

    Parameters:
        response: The HTTP response to parse

    Returns:
        The parsed JSON response data

    Raises:
        BadRequestError: For 400 status codes
        AuthenticationError: For 401 status codes
        PaymentRequiredError: For 402 status codes
        InactiveAccountError: For 403 status codes
        NotFoundError: For 404 status codes
        InternalServerError: For 500+ status codes
        NoteDxError: For other unexpected errors
    """
    try:
        data = response.json()
    except ValueError:
        data = {"detail": response.text or "No JSON content"}

    status = response.status_code
    if 200 <= status < 300:
        return data
    
    # Handle errors
    msg = data.get("message") or data.get("detail") or data
    if status == 400:
        raise BadRequestError(msg)
    elif status == 401:
        raise AuthenticationError(msg)
    elif status == 402:
        raise PaymentRequiredError(msg)
    elif status == 403:
        raise InactiveAccountError(msg)
    elif status == 404:
        raise NotFoundError(msg)
    elif status >= 500:
        raise InternalServerError(msg)
    else:
        logger.error(f"Unexpected error status={status}, data={data}")
        raise NoteDxError(f"Unexpected error: {status} {msg}")


def build_headers(token: str = None, api_key: str = None) -> Dict[str, str]:
    """Build HTTP headers for API requests.

    Parameters:
        token: Firebase ID token for authentication
        api_key: API key for direct access authentication

    Returns:
        Dictionary of headers including authorization if credentials provided
    """
    headers = {"Content-Type": "application/json"}
    
    # Firebase ID token takes precedence
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif api_key:
        headers["X-Api-Key"] = api_key
        
    return headers