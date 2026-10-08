"""Common utilities for all aig services."""

import asyncio
import hashlib
import secrets
import time
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import ParamSpec, TypeVar

T = TypeVar("T")
P = ParamSpec("P")

def generate_id(prefix: str = "", length: int = 16) -> str:
    """Generate secure random ID."""
    random_part = secrets.token_urlsafe(length)[:length]
    return f"{prefix}{random_part}" if prefix else random_part

def hash_string(data: str, algorithm: str = "sha256") -> str:
    """Hash string with specified algorithm."""
    return hashlib.new(algorithm, data.encode()).hexdigest()

def hash_file(path: Path, algorithm: str = "sha256", chunk_size: int = 8192) -> str:
    """Hash file contents."""
    hasher = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Retry decorator with exponential backoff."""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            attempt = 0
            current_delay = delay
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    time.sleep(current_delay)
                    current_delay *= backoff
        return wrapper
    return decorator

async def retry_async(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Async retry decorator with exponential backoff."""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            attempt = 0
            current_delay = delay
            while True:
                try:
                    return await func(*args, **kwargs)
                except exceptions:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
        return wrapper
    return decorator

def timer(func: Callable[P, T]) -> Callable[P, T]:
    """Timer decorator for measuring execution time."""
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        time.perf_counter() - start
        return result
    return wrapper

async def timer_async(func: Callable[P, T]) -> Callable[P, T]:
    """Async timer decorator."""
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        time.perf_counter() - start
        return result
    return wrapper

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe filesystem usage."""
    import re
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def parse_size(size_str: str) -> int:
    """Parse human-readable size string to bytes."""
    units = {"k": 1024, "m": 1024**2, "g": 1024**3, "t": 1024**4}
    size_str = size_str.strip().lower()
    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            return int(float(size_str[:-1]) * multiplier)
    return int(size_str)

def format_size(bytes_: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_ < 1024:
            return f"{bytes_:.1f}{unit}"
        bytes_ /= 1024
    return f"{bytes_:.1f}PB"
