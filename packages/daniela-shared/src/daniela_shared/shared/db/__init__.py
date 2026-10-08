"""Database connection pooling utilities.

Provides shared connection pools for Redis and SQLite to avoid
creating new connections per request.
"""

from shared.db.redis_pool import get_redis_client
from shared.db.sqlite_pool import get_sqlite_engine

__all__ = ["get_redis_client", "get_sqlite_engine"]
