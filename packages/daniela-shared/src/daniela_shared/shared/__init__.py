"""
AIG Shared - Common libraries for all aig services.

Usage:
    from shared import get_logger, get_metrics_registry, create_jwt_handler
    from shared.config import get_service_config, get_service_urls
    from shared.auth import create_jwt_handler
    from shared.errors import AppError, ValidationError
    from shared.events import get_event_bus, Event
    from shared.utils import generate_id, retry, timer
"""

from shared.auth import JWTHandler, TokenPayload, create_jwt_handler
from shared.config import (
    SERVICE_PORTS,
    ServiceConfig,
    get_database_url,
    get_jwt_secret,
    get_nats_url,
    get_redis_url,
    get_service_config,
    get_service_urls,
)
from shared.errors import (
    AppError,
    DependencyFailedError,
    ErrorCode,
    ForbiddenError,
    NotFoundError,
    RateLimitedError,
    ServiceUnavailableError,
    TimeoutError,
    UnauthorizedError,
    ValidationError,
    error_response,
    handle_error,
)
from shared.events import Event, EventBus, get_event_bus
from shared.logfmt import (
    JSONFormatter,
    get_correlation_id,
    get_logger,
    set_correlation_id,
    setup_logging,
)
from shared.metrics import MetricsRegistry, get_metrics_registry
from shared.utils import (
    format_size,
    generate_id,
    hash_file,
    hash_string,
    parse_size,
    retry,
    retry_async,
    sanitize_filename,
    timer,
    timer_async,
)

__version__ = "1.0.0"
__all__ = [
    # Config
    "ServiceConfig", "SERVICE_PORTS", "get_service_config",
    "get_database_url", "get_redis_url", "get_nats_url",
    "get_jwt_secret", "get_service_urls",
    # Auth
    "JWTHandler", "TokenPayload", "create_jwt_handler",
    # Logging
    "JSONFormatter", "setup_logging", "get_logger",  # de shared.logfmt
    "set_correlation_id", "get_correlation_id",
    # Metrics
    "MetricsRegistry", "get_metrics_registry",
    # Errors
    "ErrorCode", "AppError", "ValidationError", "NotFoundError",
    "UnauthorizedError", "ForbiddenError", "RateLimitedError",
    "ServiceUnavailableError", "TimeoutError", "DependencyFailedError",
    "handle_error", "error_response",
    # Events
    "EventBus", "Event", "get_event_bus",
    # Utils
    "generate_id", "hash_string", "hash_file",
    "retry", "retry_async", "timer", "timer_async",
    "sanitize_filename", "parse_size", "format_size",
]
