"""Error handling for all aig services."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ErrorCode(Enum):
    """Standard error codes across all services."""
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    RATE_LIMITED = "RATE_LIMITED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    DEPENDENCY_FAILED = "DEPENDENCY_FAILED"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"

@dataclass
class AppError(Exception):
    """Base application error with structured data."""
    message: str
    code: ErrorCode = ErrorCode.INTERNAL_ERROR
    details: dict[str, Any] | None = None
    status_code: int = 500

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": self.code.value,
            "message": self.message,
            "details": self.details,
        }

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"

class ValidationError(AppError):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, ErrorCode.VALIDATION_ERROR, details, 400)

class NotFoundError(AppError):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, ErrorCode.NOT_FOUND, details, 404)

class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized", details: dict[str, Any] | None = None):
        super().__init__(message, ErrorCode.UNAUTHORIZED, details, 401)

class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden", details: dict[str, Any] | None = None):
        super().__init__(message, ErrorCode.FORBIDDEN, details, 403)

class RateLimitedError(AppError):
    def __init__(self, message: str = "Rate limit exceeded", details: dict[str, Any] | None = None):
        super().__init__(message, ErrorCode.RATE_LIMITED, details, 429)

class ServiceUnavailableError(AppError):
    def __init__(self, message: str = "Service unavailable", details: dict[str, Any] | None = None):
        super().__init__(message, ErrorCode.SERVICE_UNAVAILABLE, details, 503)

class TimeoutError(AppError):
    def __init__(self, message: str = "Request timeout", details: dict[str, Any] | None = None):
        super().__init__(message, ErrorCode.TIMEOUT, details, 504)

class DependencyFailedError(AppError):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, ErrorCode.DEPENDENCY_FAILED, details, 502)

def handle_error(error: Exception) -> dict[str, Any]:
    """Convert any exception to standard error response."""
    if isinstance(error, AppError):
        return error.to_dict()
    return AppError(str(error)).to_dict()

def error_response(error: Exception) -> tuple[dict[str, Any], int]:
    """Return error response tuple for Flask."""
    if isinstance(error, AppError):
        return error.to_dict(), error.status_code
    return AppError(str(error)).to_dict(), 500
