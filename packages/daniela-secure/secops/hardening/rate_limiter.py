#!/usr/bin/env python3
"""
Advanced Rate Limiter for aig Monorepo
Sliding window log algorithm with Redis backend
Per-IP, per-user, per-endpoint with dynamic thresholds
"""

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool


class LimitStrategy(Enum):
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    SLIDING_WINDOW_LOG = "sliding_window_log"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


class LimitScope(Enum):
    IP = "ip"
    USER = "user"
    ENDPOINT = "endpoint"
    IP_ENDPOINT = "ip:endpoint"
    USER_ENDPOINT = "user:endpoint"
    GLOBAL = "global"


@dataclass
class RateLimitConfig:
    """Configuration for a rate limit rule"""
    scope: LimitScope = LimitScope.IP
    strategy: LimitStrategy = LimitStrategy.SLIDING_WINDOW_LOG
    max_requests: int = 100
    window_seconds: int = 60
    burst_allowance: int = 0
    block_duration: int = 300  # seconds to block after limit exceeded
    custom_key: str | None = None


@dataclass
class RateLimitResult:
    """Result of a rate limit check"""
    allowed: bool
    current_count: int
    max_requests: int
    remaining: int
    reset_time: float
    retry_after: int | None = None
    scope_key: str = ""
    scope_type: str = ""
    blocked_until: float | None = None


class SlidingWindowLogLimiter:
    """
    Sliding Window Log algorithm implementation.
    Most accurate but uses more memory (stores each request timestamp).
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def check_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        burst_allowance: int = 0
    ) -> RateLimitResult:
        now = time.time()
        window_start = now - window_seconds
        effective_limit = max_requests + burst_allowance

        # Use Redis sorted set to store timestamps
        redis_key = f"ratelimit:swl:{key}"

        pipe = self.redis.pipeline()
        # Remove expired entries
        pipe.zremrangebyscore(redis_key, 0, window_start)
        # Count current requests
        pipe.zcard(redis_key)
        # Add current request
        pipe.zadd(redis_key, {str(now): now})
        # Set expiry
        pipe.expire(redis_key, window_seconds + 1)
        results = await pipe.execute()

        current_count = results[1] + 1  # +1 for current request
        allowed = current_count <= effective_limit

        if not allowed:
            # Remove the request we just added since it's over limit
            await self.redis.zrem(redis_key, str(now))
            # Get oldest entry to calculate retry_after
            oldest = await self.redis.zrange(redis_key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(oldest[0][1] + window_seconds - now) + 1
            else:
                retry_after = window_seconds
            reset_time = now + retry_after
        else:
            retry_after = None
            reset_time = now + window_seconds

        return RateLimitResult(
            allowed=allowed,
            current_count=current_count if allowed else current_count - 1,
            max_requests=max_requests,
            remaining=max(0, effective_limit - current_count) if allowed else 0,
            reset_time=reset_time,
            retry_after=retry_after
        )


class SlidingWindowCounterLimiter:
    """
    Sliding Window Counter algorithm.
    More memory efficient, slight inaccuracy at window boundaries.
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def check_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        burst_allowance: int = 0
    ) -> RateLimitResult:
        now = time.time()
        current_window = int(now // window_seconds)
        previous_window = current_window - 1
        effective_limit = max_requests + burst_allowance

        current_key = f"ratelimit:swc:{key}:{current_window}"
        previous_key = f"ratelimit:swc:{key}:{previous_window}"

        pipe = self.redis.pipeline()
        pipe.get(current_key)
        pipe.get(previous_key)
        results = await pipe.execute()

        current_count = int(results[0] or 0)
        previous_count = int(results[1] or 0)

        # Weighted calculation
        prev_weight = 1 - (now % window_seconds) / window_seconds
        weighted_count = current_count + (previous_count * prev_weight)

        allowed = weighted_count < effective_limit

        if allowed:
            pipe = self.redis.pipeline()
            pipe.incr(current_key)
            pipe.expire(current_key, window_seconds * 2)
            await pipe.execute()
            current_count += 1

        remaining = max(0, int(effective_limit - weighted_count - (1 if allowed else 0)))
        reset_time = (current_window + 1) * window_seconds
        retry_after = int(reset_time - now) if not allowed else None

        return RateLimitResult(
            allowed=allowed,
            current_count=int(weighted_count) + (1 if allowed else 0),
            max_requests=max_requests,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=retry_after
        )


class TokenBucketLimiter:
    """Token Bucket algorithm for smooth rate limiting"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def check_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        burst_allowance: int = 0
    ) -> RateLimitResult:
        capacity = max_requests + burst_allowance
        refill_rate = max_requests / window_seconds  # tokens per second

        redis_key = f"ratelimit:tb:{key}"
        now = time.time()

        # Get current state
        data = await self.redis.hmget(redis_key, "tokens", "last_refill")
        tokens = float(data[0]) if data[0] else float(capacity)
        last_refill = float(data[1]) if data[1] else now

        # Refill tokens
        elapsed = now - last_refill
        tokens = min(capacity, tokens + elapsed * refill_rate)

        allowed = tokens >= 1

        if allowed:
            tokens -= 1
            await self.redis.hmset(redis_key, {"tokens": tokens, "last_refill": now})
            await self.redis.expire(redis_key, window_seconds * 2)
            remaining = int(tokens)
        else:
            remaining = 0

        reset_time = now + (1 - tokens) / refill_rate if not allowed else now + window_seconds
        retry_after = int(reset_time - now) if not allowed else None

        return RateLimitResult(
            allowed=allowed,
            current_count=capacity - int(tokens),
            max_requests=max_requests,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=retry_after
        )


class AdvancedRateLimiter:
    """
    Main rate limiter with multiple strategies and scopes.
    Supports dynamic configuration and distributed deployments.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_config: RateLimitConfig = None,
        endpoint_configs: dict[str, RateLimitConfig] = None,
        user_tier_configs: dict[str, RateLimitConfig] = None
    ):
        self.redis_url = redis_url
        self.default_config = default_config or RateLimitConfig()
        self.endpoint_configs = endpoint_configs or {}
        self.user_tier_configs = user_tier_configs or {}

        self._pool: ConnectionPool | None = None
        self._redis: redis.Redis | None = None
        self._limiters = {}

    async def initialize(self):
        """Initialize Redis connection"""
        self._pool = ConnectionPool.from_url(self.redis_url, max_connections=50)
        self._redis = redis.Redis(connection_pool=self._pool)

        # Initialize limiters
        self._limiters = {
            LimitStrategy.SLIDING_WINDOW_LOG: SlidingWindowLogLimiter(self._redis),
            LimitStrategy.SLIDING_WINDOW: SlidingWindowCounterLimiter(self._redis),
            LimitStrategy.TOKEN_BUCKET: TokenBucketLimiter(self._redis),
        }

    async def close(self):
        """Close Redis connections"""
        if self._redis:
            await self._redis.close()
        if self._pool:
            await self._pool.disconnect()

    def _get_config(self, endpoint: str, user_tier: str = None) -> RateLimitConfig:
        """Get rate limit config for endpoint/user"""
        # Check endpoint-specific config
        if endpoint in self.endpoint_configs:
            return self.endpoint_configs[endpoint]

        # Check user tier config
        if user_tier and user_tier in self.user_tier_configs:
            return self.user_tier_configs[user_tier]

        return self.default_config

    def _build_key(
        self,
        config: RateLimitConfig,
        ip: str,
        user_id: str = None,
        endpoint: str = None,
        custom_data: dict = None
    ) -> str:
        """Build rate limit key based on scope"""
        parts = ["ratelimit"]

        if config.custom_key and custom_data:
            parts.append(custom_data.get(config.custom_key, "unknown"))
        else:
            if config.scope in [LimitScope.IP, LimitScope.IP_ENDPOINT]:
                parts.append(f"ip:{ip}")
            if config.scope in [LimitScope.USER, LimitScope.USER_ENDPOINT]:
                parts.append(f"user:{user_id or 'anonymous'}")
            if config.scope in [LimitScope.ENDPOINT, LimitScope.IP_ENDPOINT, LimitScope.USER_ENDPOINT]:
                parts.append(f"ep:{endpoint or 'unknown'}")
            if config.scope == LimitScope.GLOBAL:
                parts.append("global")

        return ":".join(parts)

    async def check_limit(
        self,
        ip: str,
        endpoint: str,
        user_id: str = None,
        user_tier: str = None,
        custom_data: dict = None,
        method: str = "GET"
    ) -> RateLimitResult:
        """Check rate limit for a request"""
        if not self._redis:
            await self.initialize()

        config = self._get_config(endpoint, user_tier)
        limiter = self._limiters.get(config.strategy, self._limiters[LimitStrategy.SLIDING_WINDOW_LOG])

        key = self._build_key(config, ip, user_id, endpoint, custom_data)

        result = await limiter.check_limit(
            key=key,
            max_requests=config.max_requests,
            window_seconds=config.window_seconds,
            burst_allowance=config.burst_allowance
        )

        result.scope_key = key
        result.scope_type = config.scope.value

        # Handle blocking
        if not result.allowed and config.block_duration > 0:
            block_key = f"ratelimit:block:{key}"
            await self._redis.setex(block_key, config.block_duration, "1")
            result.blocked_until = time.time() + config.block_duration

        return result

    async def is_blocked(self, ip: str, endpoint: str, user_id: str = None) -> bool:
        """Check if IP/user is currently blocked"""
        if not self._redis:
            await self.initialize()

        config = self._get_config(endpoint)
        key = self._build_key(config, ip, user_id, endpoint)
        block_key = f"ratelimit:block:{key}"

        return await self._redis.exists(block_key) > 0

    async def get_current_usage(
        self,
        ip: str,
        endpoint: str,
        user_id: str = None,
        user_tier: str = None
    ) -> dict[str, Any]:
        """Get current usage statistics"""
        if not self._redis:
            await self.initialize()

        config = self._get_config(endpoint, user_tier)
        key = self._build_key(config, ip, user_id, endpoint)

        # Get stats from sliding window log
        now = time.time()
        window_start = now - config.window_seconds
        redis_key = f"ratelimit:swl:{key}"

        count = await self._redis.zcount(redis_key, window_start, now)
        oldest = await self._redis.zrange(redis_key, 0, 0, withscores=True)

        return {
            "current_requests": count,
            "max_requests": config.max_requests,
            "window_seconds": config.window_seconds,
            "remaining": max(0, config.max_requests - count),
            "oldest_request": oldest[0][1] if oldest else None,
            "reset_time": now + config.window_seconds
        }

    async def reset_limit(self, ip: str, endpoint: str, user_id: str = None):
        """Manually reset rate limit for a key"""
        if not self._redis:
            await self.initialize()

        config = self._get_config(endpoint)
        key = self._build_key(config, ip, user_id, endpoint)

        patterns = [
            f"ratelimit:swl:{key}",
            f"ratelimit:swc:{key}:*",
            f"ratelimit:tb:{key}",
            f"ratelimit:block:{key}"
        ]

        for pattern in patterns:
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)

    async def get_blocked_ips(self, limit: int = 100) -> list[dict]:
        """Get currently blocked IPs"""
        if not self._redis:
            await self.initialize()

        blocked = []
        cursor = 0
        while len(blocked) < limit:
            cursor, keys = await self._redis.scan(cursor, match="ratelimit:block:*", count=100)
            for key in keys:
                ttl = await self._redis.ttl(key)
                blocked.append({
                    "key": key.decode() if isinstance(key, bytes) else key,
                    "blocked_until": time.time() + ttl if ttl > 0 else None
                })
            if cursor == 0:
                break

        return blocked[:limit]


# Flask/FastAPI integration middleware
class RateLimitMiddleware:
    """ASGI/WSGI middleware for rate limiting"""

    def __init__(
        self,
        app,
        rate_limiter: AdvancedRateLimiter,
        excluded_paths: list[str] = None,
        header_prefix: str = "X-RateLimit"
    ):
        self.app = app
        self.rate_limiter = rate_limiter
        self.excluded_paths = excluded_paths or ["/health", "/metrics", "/favicon.ico"]
        self.header_prefix = header_prefix

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            await self.app(scope, receive, send)
            return

        # Extract client IP
        client = scope.get("client")
        ip = client[0] if client else "unknown"

        # Extract headers
        headers = dict(scope.get("headers", []))
        user_id = headers.get(b"x-user-id", b"").decode() if b"x-user-id" in headers else None
        user_tier = headers.get(b"x-user-tier", b"").decode() if b"x-user-tier" in headers else None

        # Check rate limit
        result = await self.rate_limiter.check_limit(
            ip=ip,
            endpoint=path,
            user_id=user_id,
            user_tier=user_tier,
            method=scope.get("method", "GET")
        )

        # Add rate limit headers
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers_list = list(message.get("headers", []))
                headers_list.extend([
                    (f"{self.header_prefix}-Limit".encode(), str(result.max_requests).encode()),
                    (f"{self.header_prefix}-Remaining".encode(), str(result.remaining).encode()),
                    (f"{self.header_prefix}-Reset".encode(), str(int(result.reset_time)).encode()),
                    (f"{self.header_prefix}-Scope".encode(), result.scope_type.encode()),
                ])
                if result.retry_after:
                    headers_list.append((b"Retry-After", str(result.retry_after).encode()))
                message["headers"] = headers_list

            await send(message)

        if not result.allowed:
            # Return 429 Too Many Requests
            await send({
                "type": "http.response.start",
                "status": 429,
                "headers": [
                    (b"Content-Type", b"application/json"),
                    (f"{self.header_prefix}-Limit".encode(), str(result.max_requests).encode()),
                    (f"{self.header_prefix}-Remaining".encode(), b"0"),
                    (f"{self.header_prefix}-Reset".encode(), str(int(result.reset_time)).encode()),
                    (b"Retry-After", str(result.retry_after or 60).encode()),
                ]
            })
            await send({
                "type": "http.response.body",
                "body": b'{"error": "Rate limit exceeded", "retry_after": ' + str(result.retry_after or 60).encode() + b'}'
            })
            return

        await self.app(scope, receive, send_with_headers)


# Decorator for endpoint-specific limits
def rate_limit(config: RateLimitConfig):
    """Decorator to apply rate limit to specific endpoint"""
    def decorator(func):
        func._rate_limit_config = config
        return func
    return decorator


# Default configurations for aig
DEFAULT_ENDPOINT_CONFIGS = {
    "/api/auth/login": RateLimitConfig(
        scope=LimitScope.IP,
        max_requests=5,
        window_seconds=300,
        block_duration=900
    ),
    "/api/auth/register": RateLimitConfig(
        scope=LimitScope.IP,
        max_requests=3,
        window_seconds=3600,
        block_duration=3600
    ),
    "/api/auth/password/reset": RateLimitConfig(
        scope=LimitScope.IP,
        max_requests=2,
        window_seconds=3600,
        block_duration=7200
    ),
    "/api/upload": RateLimitConfig(
        scope=LimitScope.USER,
        max_requests=10,
        window_seconds=3600,
        burst_allowance=5
    ),
    "/api/files": RateLimitConfig(
        scope=LimitScope.USER,
        max_requests=50,
        window_seconds=60
    ),
    "/api/search": RateLimitConfig(
        scope=LimitScope.USER,
        max_requests=30,
        window_seconds=60
    ),
    "/api/admin": RateLimitConfig(
        scope=LimitScope.USER,
        max_requests=100,
        window_seconds=60
    ),
}

DEFAULT_USER_TIER_CONFIGS = {
    "free": RateLimitConfig(max_requests=50, window_seconds=60),
    "basic": RateLimitConfig(max_requests=100, window_seconds=60),
    "pro": RateLimitConfig(max_requests=500, window_seconds=60),
    "enterprise": RateLimitConfig(max_requests=2000, window_seconds=60),
}


async def create_rate_limiter(
    redis_url: str = "redis://localhost:6379/0"
) -> AdvancedRateLimiter:
    """Factory function to create configured rate limiter"""
    limiter = AdvancedRateLimiter(
        redis_url=redis_url,
        default_config=RateLimitConfig(max_requests=100, window_seconds=60),
        endpoint_configs=DEFAULT_ENDPOINT_CONFIGS,
        user_tier_configs=DEFAULT_USER_TIER_CONFIGS
    )
    await limiter.initialize()
    return limiter


if __name__ == "__main__":
    async def demo():
        limiter = await create_rate_limiter("redis://localhost:6379/0")

        # Test rate limiting
        for i in range(15):
            result = await limiter.check_limit("192.168.1.100", "/api/auth/login")
            print(f"Request {i+1}: allowed={result.allowed}, remaining={result.remaining}, retry_after={result.retry_after}")
            if not result.allowed:
                break
            await asyncio.sleep(0.1)

        await limiter.close()

    asyncio.run(demo())
