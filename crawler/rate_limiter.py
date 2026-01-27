"""Rate limiter for controlling request frequency."""
import asyncio
import time
from typing import Optional


class RateLimiter:
    """Async rate limiter to control request frequency."""

    def __init__(self, delay: float = 1.0, max_concurrent: int = 5):
        """
        Initialize rate limiter.

        Args:
            delay: Minimum delay between requests in seconds.
            max_concurrent: Maximum number of concurrent requests.
        """
        self.delay = delay
        self.max_concurrent = max_concurrent
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._last_request_time: float = 0
        self._lock: Optional[asyncio.Lock] = None

    async def _ensure_initialized(self) -> None:
        """Ensure async primitives are initialized."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
        if self._lock is None:
            self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire permission to make a request."""
        await self._ensure_initialized()
        
        await self._semaphore.acquire()
        
        async with self._lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            
            if time_since_last < self.delay:
                wait_time = self.delay - time_since_last
                await asyncio.sleep(wait_time)
            
            self._last_request_time = time.time()

    def release(self) -> None:
        """Release the semaphore after request completion."""
        if self._semaphore is not None:
            self._semaphore.release()

    async def __aenter__(self) -> "RateLimiter":
        """Async context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        self.release()
