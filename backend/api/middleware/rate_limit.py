"""
Simple in-process rate limiter middleware.

Uses a sliding-window counter keyed by client IP.  Falls back gracefully if
the optional `redis` client is unavailable (counter lives in-process only).
"""

import time
from collections import defaultdict, deque
from threading import Lock
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter: `requests_per_minute` calls per IP per 60 s."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self._rpm = requests_per_minute
        self._window = 60.0  # seconds
        self._counters: dict[str, deque] = defaultdict(deque)
        self._lock = Lock()

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    async def dispatch(self, request: Request, call_next: Callable):
        ip = self._get_client_ip(request)
        now = time.monotonic()
        cutoff = now - self._window

        with self._lock:
            timestamps = self._counters[ip]
            # Drop timestamps outside the window
            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()
            if len(timestamps) >= self._rpm:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"Rate limit exceeded: max {self._rpm} requests per minute."
                    },
                    headers={"Retry-After": "60"},
                )
            timestamps.append(now)

        return await call_next(request)
