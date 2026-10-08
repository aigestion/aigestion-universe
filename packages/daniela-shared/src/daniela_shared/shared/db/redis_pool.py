"""Shared Redis connection pool.

Usage:
    from shared.db import get_redis_client
    r = get_redis_client()
    r.set("key", "value")
"""

import redis

from shared.config import get_redis_url

_pool = None


def get_redis_client() -> redis.Redis:
    """Get a Redis client backed by a shared connection pool.

    The pool is created lazily on first call and reused across all
    callers in the same process.
    """
    global _pool
    if _pool is None:
        _pool = redis.ConnectionPool.from_url(
            get_redis_url(),
            max_connections=20,
            decode_responses=True,
        )
    return redis.Redis(connection_pool=_pool)
