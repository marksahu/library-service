"""
app/core/middleware.py

- RequestContextMiddleware: generates a UUID request_id for every request,
  binds it into structlog contextvars so every log line emitted during that
  request carries the same request_id automatically.
- Also logs method, path, status code, and elapsed time for each request.
"""
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import structlog.contextvars

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())

        # Bind request_id so every log inside this request includes it
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start = time.perf_counter()
        response = None
        try:
            response = await call_next(request)
        except Exception:
            logger.warning(
                "unhandled_exception",
                method=request.method,
                path=request.url.path,
            )
            raise
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            status_code = response.status_code if response is not None else 500
            logger.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                elapsed_ms=elapsed_ms,
            )

        response.headers["X-Request-ID"] = request_id
        return response
