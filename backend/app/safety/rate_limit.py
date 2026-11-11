"""Very small in-memory rate limiter (spec §12, "Abuse/cost").

Allows RATE_LIMIT_PER_MINUTE requests per client IP in any rolling 60-second window
for the /api routes. It is middleware, not an endpoint, so the app still exposes
exactly two application routes. Memory only: nothing is stored on disk, and it resets
when the server restarts. Good enough for a single-server demo.
"""

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.errors import error_body

WINDOW_SECONDS = 60.0


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit_per_minute: int) -> None:
        super().__init__(app)
        self.limit = limit_per_minute
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        # Only count real API calls (not CORS preflight requests or /docs).
        if self.limit <= 0 or request.method != "POST" or not request.url.path.startswith("/api/"):
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = self.hits[ip]
        while window and now - window[0] > WINDOW_SECONDS:
            window.popleft()
        if len(window) >= self.limit:
            retry_after = int(WINDOW_SECONDS - (now - window[0])) + 1
            return JSONResponse(
                status_code=429,
                content=error_body(
                    "RATE_LIMITED",
                    "Too many requests, please wait a moment and try again.",
                    {"retry_after_seconds": retry_after},
                ),
                headers={"Retry-After": str(retry_after)},
            )
        window.append(now)
        return await call_next(request)
