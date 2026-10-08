"""AI response cache with hash-based dedup and optional Redis backend."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A cached AI response."""

    response: dict[str, Any]
    timestamp: float
    ttl: float

    @property
    def is_expired(self) -> bool:
        return time.time() > self.timestamp + self.ttl


class AICache:
    """Cache for LLM responses with hash-based dedup and TTL expiry.

    Uses Redis if available, falls back to in-memory dict.
    """

    def __init__(self, default_ttl: float = 3600.0, redis_url: str | None = None) -> None:
        self._default_ttl = default_ttl
        self._memory_cache: dict[str, CacheEntry] = {}
        self._redis_client = None
        if redis_url:
            try:
                from core.data.db_optimizer import get_redis_client
                self._redis_client = get_redis_client()
                self._redis_client.ping()
                logger.info("AICache connected to Redis (shared pool)")
            except Exception as e:
                logger.warning("Redis unavailable, using in-memory cache: %s", e)
                self._redis_client = None

    @staticmethod
    def hash_prompt(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]

    def get(self, prompt_hash: str) -> dict[str, Any] | None:
        if self._redis_client:
            try:
                raw = self._redis_client.get(f"ai_cache:{prompt_hash}")
                if raw:
                    entry = json.loads(raw)
                    if time.time() <= entry.get("timestamp", 0) + entry.get("ttl", 0):
                        return entry.get("response")
                    self._redis_client.delete(f"ai_cache:{prompt_hash}")
                return None
            except Exception:
                pass

        entry = self._memory_cache.get(prompt_hash)
        if entry is None:
            return None
        if entry.is_expired:
            del self._memory_cache[prompt_hash]
            return None
        return entry.response

    def set(self, prompt_hash: str, response: dict[str, Any], ttl: float | None = None) -> None:
        ttl = ttl if ttl is not None else self._default_ttl

        if self._redis_client:
            try:
                payload = json.dumps({"response": response, "timestamp": time.time(), "ttl": ttl})
                self._redis_client.setex(f"ai_cache:{prompt_hash}", int(ttl), payload)
                return
            except Exception:
                pass

        self._memory_cache[prompt_hash] = CacheEntry(response=response, timestamp=time.time(), ttl=ttl)

    def invalidate(self, prompt_hash: str) -> bool:
        removed = False
        if self._redis_client:
            try:
                self._redis_client.delete(f"ai_cache:{prompt_hash}")
                removed = True
            except Exception:
                pass

        if prompt_hash in self._memory_cache:
            del self._memory_cache[prompt_hash]
            removed = True
        return removed

    def clear(self) -> int:
        count = len(self._memory_cache)
        self._memory_cache.clear()
        if self._redis_client:
            try:
                keys = self._redis_client.keys("ai_cache:*")
                if keys:
                    self._redis_client.delete(*keys)
                    count += len(keys)
            except Exception:
                pass
        return count

    def size(self) -> int:
        if self._redis_client:
            try:
                return len(self._redis_client.keys("ai_cache:*"))
            except Exception:
                pass
        return len(self._memory_cache)

    def cleanup_expired(self) -> int:
        """Remove expired entries from memory cache."""
        expired_keys = [k for k, v in self._memory_cache.items() if v.is_expired]
        for k in expired_keys:
            del self._memory_cache[k]
        return len(expired_keys)
