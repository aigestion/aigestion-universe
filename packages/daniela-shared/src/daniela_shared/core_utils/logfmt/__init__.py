"""Structured logging for all aig services."""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime

# Context variable for correlation ID
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)

class JSONFormatter(logging.Formatter):
    """JSON log formatter with correlation ID support."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation ID if available
        corr_id = correlation_id_var.get()
        if corr_id:
            log_obj["correlation_id"] = corr_id

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {"name", "msg", "args", "levelname", "levelno", "pathname",
                          "filename", "module", "lineno", "funcName", "created",
                          "msecs", "relativeCreated", "thread", "threadName",
                          "processName", "process", "getMessage", "exc_info",
                          "exc_text", "stack_info"}:
                log_obj[key] = value

        return json.dumps(log_obj, ensure_ascii=False)

def setup_logging(service_name: str, level: str = "INFO", json_format: bool = True) -> logging.Logger:
    """Setup structured logging for a service."""
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        ))
    logger.addHandler(handler)
    logger.propagate = False

    return logger

def get_logger(name: str) -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)

def set_correlation_id(corr_id: str) -> None:
    """Set correlation ID for current context."""
    correlation_id_var.set(corr_id)

def get_correlation_id() -> str | None:
    """Get correlation ID for current context."""
    return correlation_id_var.get()
