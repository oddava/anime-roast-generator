"""Thread-safe cache implementation with TTL-based eviction."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A single cache entry with data and timestamp."""

    data: Any
    timestamp: datetime
    access_count: int = 0


class TimedCache:
    """Thread-safe cache with TTL-based eviction and size limits.

    Features:
    - Automatic TTL-based expiration
    - LRU eviction when size limit reached
    - Thread-safe async operations
    - Periodic cleanup of expired entries
    """

    def __init__(
        self,
        ttl_seconds: int = 3600,
        max_size: int = 1000,
        cleanup_interval: int = 300,  # 5 minutes
    ):
        self._cache: Dict[str, CacheEntry] = {}
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._cleanup_interval = cleanup_interval
        self._lock = asyncio.Lock()
        self._last_cleanup = datetime.now()

    async def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired.

        Args:
            key: Cache key to look up

        Returns:
            Cached data or None if not found/expired
        """
        async with self._lock:
            # Periodic cleanup check
            if (datetime.now() - self._last_cleanup).seconds > self._cleanup_interval:
                await self._cleanup_expired()

            if key not in self._cache:
                return None

            entry = self._cache[key]

            # Check if expired
            if datetime.now() - entry.timestamp > timedelta(seconds=self._ttl):
                del self._cache[key]
                logger.debug(f"Cache entry expired and removed: {key[:16]}...")
                return None

            # Update access count for LRU
            entry.access_count += 1
            return entry.data

    async def set(self, key: str, data: Any) -> None:
        """Set cache value with automatic eviction if at capacity.

        Args:
            key: Cache key
            data: Data to cache
        """
        async with self._lock:
            # Evict oldest entries if at capacity (LRU strategy)
            while len(self._cache) >= self._max_size:
                # Find least recently used entry (lowest access count, oldest timestamp)
                oldest_key = min(
                    self._cache.keys(),
                    key=lambda k: (
                        self._cache[k].access_count,
                        self._cache[k].timestamp,
                    ),
                )
                del self._cache[oldest_key]
                logger.debug(f"Evicted LRU cache entry: {oldest_key[:16]}...")

            self._cache[key] = CacheEntry(
                data=data, timestamp=datetime.now(), access_count=0
            )

    async def delete(self, key: str) -> bool:
        """Delete a specific cache entry.

        Args:
            key: Cache key to delete

        Returns:
            True if key existed and was deleted, False otherwise
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")

    async def _cleanup_expired(self) -> int:
        """Remove all expired entries. Called periodically.

        Returns:
            Number of entries removed
        """
        now = datetime.now()
        expired_keys = [
            k
            for k, entry in self._cache.items()
            if now - entry.timestamp > timedelta(seconds=self._ttl)
        ]

        for key in expired_keys:
            del self._cache[key]

        self._last_cleanup = now

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def get_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "ttl_seconds": self._ttl,
            "utilization": len(self._cache) / self._max_size
            if self._max_size > 0
            else 0,
        }


# Global cache instance
_response_cache: Optional[TimedCache] = None


def get_cache() -> TimedCache:
    """Get or create the global cache instance.

    Returns:
        TimedCache instance
    """
    global _response_cache
    if _response_cache is None:
        _response_cache = TimedCache(
            ttl_seconds=3600,  # 1 hour
            max_size=1000,
            cleanup_interval=300,  # 5 minutes
        )
    return _response_cache


async def clear_cache() -> None:
    """Clear the global cache."""
    cache = get_cache()
    await cache.clear()
