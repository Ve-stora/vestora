"""
Vestora In-Memory TTL Cache
============================
Simple async-compatible TTL cache for market data.

Interface mirrors what a Redis client would expose — so swapping to
redis-py in production only requires changing this module, nothing else.

Thread-safe via asyncio.Lock. Suitable for single-process Uvicorn workers.
For multi-worker deployments: replace with Redis (redis-py async client).
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Cache entry: (value, expires_at_monotonic) ──────────────────────────────

_store:      Dict[str, Tuple[Any, float]] = {}
_store_lock: asyncio.Lock                  = asyncio.Lock()


# ── Public API ───────────────────────────────────────────────────────────────

async def cache_get(key: str) -> Optional[Any]:
    """
    Retrieve value for key. Returns None if key is missing or expired.
    Expired entries are deleted on access (lazy eviction).
    """
    async with _store_lock:
        entry = _store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            del _store[key]
            logger.debug("Cache miss (expired): %s", key)
            return None
        logger.debug("Cache hit: %s", key)
        return value


async def cache_set(key: str, value: Any, ttl: int) -> None:
    """
    Store value under key with TTL in seconds.
    ttl=0 means no expiry (stored indefinitely until cleared).
    """
    expires_at = time.monotonic() + ttl if ttl > 0 else float("inf")
    async with _store_lock:
        _store[key] = (value, expires_at)
    logger.debug("Cache set: %s (ttl=%ds)", key, ttl)


async def cache_delete(key: str) -> None:
    """Remove a single key from cache."""
    async with _store_lock:
        _store.pop(key, None)
    logger.debug("Cache delete: %s", key)


async def cache_clear_prefix(prefix: str) -> int:
    """
    Delete all keys starting with prefix.
    Returns number of keys deleted.
    Useful for invalidating a whole exchange's data: cache_clear_prefix("stocks:NSE")
    """
    async with _store_lock:
        to_delete = [k for k in _store if k.startswith(prefix)]
        for k in to_delete:
            del _store[k]
    if to_delete:
        logger.info("Cache cleared %d keys with prefix '%s'", len(to_delete), prefix)
    return len(to_delete)


async def cache_clear_all() -> None:
    """Flush entire cache. Use with care."""
    async with _store_lock:
        count = len(_store)
        _store.clear()
    logger.info("Cache flushed — %d entries cleared", count)


async def cache_stats() -> Dict[str, Any]:
    """Return diagnostic stats about current cache state."""
    now = time.monotonic()
    async with _store_lock:
        total   = len(_store)
        expired = sum(1 for _, (_, exp) in _store.items() if now > exp)
        live    = total - expired
    return {
        "total_keys":   total,
        "live_keys":    live,
        "expired_keys": expired,
    }