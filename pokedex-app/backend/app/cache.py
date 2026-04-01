import asyncio
import time
from typing import Any


class TTLCache:
    """Simple async-safe in-memory cache with per-entry TTL."""

    def __init__(self, ttl: int = 3600) -> None:
        self._ttl = ttl
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, ts = entry
            if time.monotonic() - ts > self._ttl:
                del self._store[key]
                return None
            return value

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._store[key] = (value, time.monotonic())

    async def evict_expired(self) -> None:
        now = time.monotonic()
        async with self._lock:
            expired = [k for k, (_, ts) in self._store.items() if now - ts > self._ttl]
            for k in expired:
                del self._store[k]


# Module-level singleton — shared across all requests in one worker process
pokemon_cache = TTLCache()
