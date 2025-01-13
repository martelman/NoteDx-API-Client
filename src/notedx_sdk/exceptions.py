from typing import Optional, Dict, Any

class NoteDxError(Exception):
    """Base exception for all NoteDx API errors.

    Parameters:
        message: The error message
        code: The error code (optional)
        details: Additional error details (optional)
    """
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

class AuthenticationError(NoteDxError):
    """Error raised when authentication fails (401).

    Common error codes:
    * `UNAUTHORIZED` - Generic authentication failure
    * `USER_NOT_FOUND` - Firebase user not found
    * `INVALID_CREDENTIALS` - Invalid email/password
    * `INVALID_API_KEY` - Invalid API key
    * `TOKEN_EXPIRED` - Firebase token expired
    * `TOKEN_INVALID` - Invalid Firebase token
    """
    def __init__(self, message: str, code: str = 'UNAUTHORIZED', details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class AuthorizationError(NoteDxError):
    """Error raised when user lacks permissions (403).

    Common error codes:
    * `FORBIDDEN` - Generic authorization failure
    * `INSUFFICIENT_PERMISSIONS` - User lacks required permissions
    * `TOKEN_REVOKED` - Firebase token was revoked
    """
    def __init__(self, message: str, code: str = 'FORBIDDEN', details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class PaymentRequiredError(NoteDxError):
    """Error raised when payment is required (402).

    Common error codes:
    * `PAYMENT_REQUIRED` - Account payment is required
    * `SUBSCRIPTION_EXPIRED` - Account subscription has expired
    * `USAGE_LIMIT` - Account has exceeded usage limits
    """
    def __init__(self, message: str, code: str = 'PAYMENT_REQUIRED', details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class InactiveAccountError(NoteDxError):
    """Error raised when account is inactive (403).

    Common error codes:
    * `ACCOUNT_INACTIVE` - Account is inactive
    * `ACCOUNT_DISABLED` - Firebase account is disabled
    """
    def __init__(self, message: str, code: str = 'ACCOUNT_INACTIVE', details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class BadRequestError(NoteDxError):
    """Error raised for general bad request errors (400) that aren't validation specific.

    Common error codes:
    * `INVALID_REQUEST` - Generic invalid request
    * `INVALID_PASSWORD` - Password doesn't meet requirements
    * `EMAIL_EXISTS` - Email already exists
    * `WEAK_PASSWORD` - Password is too weak
    """
    def __init__(self, message: str, code: str = 'INVALID_REQUEST', details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class ValidationError(NoteDxError):
    """Error raised for invalid input (400).

    Parameters:
        message: The validation error message
        field: The field that failed validation (optional)
        code: The error code (defaults to 'INVALID_FIELD')
        details: Additional error details (optional)
    """
    def __init__(self, message: str, field: Optional[str] = None, code: str = 'INVALID_FIELD', details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if field:
            details['field'] = field
        super().__init__(message, code, details)

class MissingFieldError(ValidationError):
    """Error raised when required field is missing (400).

    Parameters:
        field: The name of the missing field
        details: Additional error details (optional)
    """
    def __init__(self, field: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"Missing required field: {field}", field, 'MISSING_FIELD', details)

class InvalidFieldError(ValidationError):
    """Error raised when field value is invalid (400).

    Parameters:
        field: The name of the invalid field
        message: The validation error message
        details: Additional error details (optional)
    """
    def __init__(self, field: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, field, 'INVALID_FIELD', details)

class NetworkError(NoteDxError):
    """Error raised for network connectivity issues.

    Common error codes:
    * `NETWORK_ERROR` - Generic network error
    * `TIMEOUT` - Request timed out
    * `CONNECTION_ERROR` - Failed to connect to server
    """
    def __init__(self, message: str, code: str = 'NETWORK_ERROR', details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class UploadError(NoteDxError):
    """Error raised when file upload fails.

    Parameters:
        message: The error message
        job_id: The ID of the failed upload job (optional)
        code: The error code (defaults to 'UPLOAD_ERROR')
        details: Additional error details (optional)
    """
    def __init__(self, message: str, job_id: Optional[str] = None, code: str = 'UPLOAD_ERROR', details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if job_id:
            details['job_id'] = job_id
        super().__init__(message, code, details)

class NotFoundError(NoteDxError):
    """Error raised when resource is not found (404).

    Parameters:
        message: The error message
        code: The error code (defaults to 'NOT_FOUND')
        details: Additional error details (optional)
    """
    def __init__(self, message: str, code: str = 'NOT_FOUND', details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class JobNotFoundError(NotFoundError):
    """Error raised when job is not found (404).

    Parameters:
        job_id: The ID of the job that wasn't found
        message: Custom error message (optional)
        details: Additional error details (optional)
    """
    def __init__(self, job_id: str, message: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        message = "Job not found"
        super().__init__(message, 'JOB_NOT_FOUND', {'job_id': job_id, **(details or {})})

class JobError(NoteDxError):
    """Error raised for job-related errors.

    Parameters:
        message: The error message
        job_id: The ID of the failed job
        status: The job status when error occurred (optional)
        code: The error code (defaults to 'JOB_ERROR')
        details: Additional error details (optional)
    """
    def __init__(self, message: str, job_id: str, status: Optional[str] = None, code: str = 'JOB_ERROR', details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details['job_id'] = job_id
        if status:
            details['status'] = status
        super().__init__(message, code, details)

class RateLimitError(NoteDxError):
    """Error raised when rate limit is exceeded (429).

    Parameters:
        message: The error message
        reset_time: When the rate limit will reset (optional)
        code: The error code (defaults to 'RATE_LIMIT')
        details: Additional error details (optional)
    """
    def __init__(self, message: str, reset_time: Optional[str] = None, code: str = 'RATE_LIMIT', details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if reset_time:
            details['reset_time'] = reset_time
        super().__init__(message, code, details)

class InternalServerError(NoteDxError):
    """Error raised for server-side errors (500).

    Parameters:
        message: The error message
        code: The error code (defaults to 'INTERNAL_ERROR')
        details: Additional error details (optional)
    """
    def __init__(self, message: str, code: str = 'INTERNAL_ERROR', details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class ServiceUnavailableError(NoteDxError):
    """Error raised when service is unavailable (503).

    Parameters:
        message: The error message
        code: The error code (defaults to 'SERVICE_UNAVAILABLE')
        details: Additional error details (optional)
    """
    def __init__(self, message: str, code: str = 'SERVICE_UNAVAILABLE', details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)