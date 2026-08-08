"""Hosted-demo security middleware: API keys + simple in-memory rate limit."""

from __future__ import annotations

import os
import time
from collections import defaultdict
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


def _api_keys() -> set[str]:
    raw = os.environ.get("QUANTAURA_API_KEYS", "")
    return {k.strip() for k in raw.split(",") if k.strip()}


PUBLIC_PREFIXES = ("/health", "/docs", "/openapi.json", "/redoc")


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        keys = _api_keys()
        if not keys:
            return await call_next(request)
        path = request.url.path
        if path == "/" or any(path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)
        provided = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
        if not provided or provided not in keys:
            return JSONResponse({"detail": "Invalid or missing X-API-Key"}, status_code=401)
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, per_minute: int | None = None) -> None:
        super().__init__(app)
        try:
            self.per_minute = (
                per_minute
                if per_minute is not None
                else int(os.environ.get("QUANTAURA_RATE_LIMIT_PER_MIN", "0"))
            )
        except ValueError:
            self.per_minute = 0
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if self.per_minute <= 0:
            return await call_next(request)
        client = request.client.host if request.client else "unknown"
        now = time.time()
        self._hits[client] = [t for t in self._hits[client] if now - t < 60.0]
        if len(self._hits[client]) >= self.per_minute:
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        self._hits[client].append(now)
        return await call_next(request)
