from typing import Optional, Dict, Any

class NoteDxError(Exception):
    """Base exception for all NoteDx API errors."""
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

class AuthenticationError(NoteDxError):
    """
    Raised when authentication fails (401).
    
    Common error codes:
    - UNAUTHORIZED: Generic authentication failure
    - USER_NOT_FOUND: Firebase user not found
    - INVALID_CREDENTIALS: Invalid email/password
    - INVALID_API_KEY: Invalid API key
    - TOKEN_EXPIRED: Firebase token expired
    - TOKEN_INVALID: Invalid Firebase token
    """
    def __init__(self, message: str, code: str = 'UNAUTHORIZED', details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class AuthorizationError(NoteDxError):
    """
    Raised when user lacks permissions (403).
    
    Common error codes:
    - FORBIDDEN: Generic authorization failure
    - INSUFFICIENT_PERMISSIONS: User lacks required permissions
    - TOKEN_REVOKED: Firebase token was revoked
    """
    def __init__(self, message: str, code: str = 'FORBIDDEN', details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class PaymentRequiredError(NoteDxError):
    """Raised when payment is required (402)."""
    def __init__(self, message: str, code: str = 'PAYMENT_REQUIRED', details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class InactiveAccountError(NoteDxError):
    """
    Raised when account is inactive (403).
    
    Common error codes:
    - ACCOUNT_INACTIVE: Account is inactive
    - ACCOUNT_DISABLED: Firebase account is disabled
    """
    def __init__(self, message: str, code: str = 'ACCOUNT_INACTIVE', details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class BadRequestError(NoteDxError):
    """
    Raised for general bad request errors (400) that aren't validation specific.
    
    Common error codes:
    - INVALID_REQUEST: Generic invalid request
    - INVALID_PASSWORD: Password doesn't meet requirements
    - EMAIL_EXISTS: Email already exists
    - WEAK_PASSWORD: Password is too weak
    """
    def __init__(self, message: str, code: str = 'INVALID_REQUEST', details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class ValidationError(NoteDxError):
    """Raised for invalid input (400)."""
    def __init__(self, message: str, field: Optional[str] = None, code: str = 'INVALID_FIELD', details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if field:
            details['field'] = field
        super().__init__(message, code, details)

class MissingFieldError(ValidationError):
    """Raised when required field is missing (400)."""
    def __init__(self, field: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"Missing required field: {field}", field, 'MISSING_FIELD', details)

class InvalidFieldError(ValidationError):
    """Raised when field value is invalid (400)."""
    def __init__(self, field: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, field, 'INVALID_FIELD', details)

class NetworkError(NoteDxError):
    """Raised for network connectivity issues."""
    def __init__(self, message: str, code: str = 'NETWORK_ERROR', details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class UploadError(NoteDxError):
    """Raised when file upload fails."""
    def __init__(self, message: str, job_id: Optional[str] = None, code: str = 'UPLOAD_ERROR', details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if job_id:
            details['job_id'] = job_id
        super().__init__(message, code, details)

class NotFoundError(NoteDxError):
    """Raised when resource is not found (404)."""
    def __init__(self, message: str, code: str = 'NOT_FOUND', details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class JobNotFoundError(NotFoundError):
    """Raised when job is not found (404)."""
    def __init__(self, job_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"Job {job_id} not found", 'JOB_NOT_FOUND', {'job_id': job_id, **(details or {})})

class JobError(NoteDxError):
    """Raised for job-related errors."""
    def __init__(self, message: str, job_id: str, status: Optional[str] = None, code: str = 'JOB_ERROR', details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details['job_id'] = job_id
        if status:
            details['status'] = status
        super().__init__(message, code, details)

class RateLimitError(NoteDxError):
    """Raised when rate limit is exceeded (429)."""
    def __init__(self, message: str, reset_time: Optional[str] = None, code: str = 'RATE_LIMIT', details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if reset_time:
            details['reset_time'] = reset_time
        super().__init__(message, code, details)

class InternalServerError(NoteDxError):
    """Raised for server-side errors (500)."""
    def __init__(self, message: str, code: str = 'INTERNAL_ERROR', details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class ServiceUnavailableError(NoteDxError):
    """Raised when service is unavailable (503)."""
    def __init__(self, message: str, code: str = 'SERVICE_UNAVAILABLE', details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)