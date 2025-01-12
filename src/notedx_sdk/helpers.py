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
    """Fetch an environment variable or return a default."""
    return os.environ.get(key, default)


def parse_response(response: requests.Response) -> Dict[str, Any]:
    """Convert a requests.Response to dict; raise typed errors."""
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
    """
    Assemble the appropriate headers for a request.
    
    Args:
        token: Firebase ID token
        api_key: API key for direct access
        
    Returns:
        Dict of headers including authorization if credentials provided
    """
    headers = {"Content-Type": "application/json"}
    
    # Firebase ID token takes precedence
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif api_key:
        headers["X-Api-Key"] = api_key
        
    return headers