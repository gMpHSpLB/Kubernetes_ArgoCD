"""
This code adds Prometheus metrics to a FastAPI
app by measuring every request’s count and latency,
then exposing those metrics at a /metrics-style
endpoint in Prometheus format.
"""

import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

# Metrics: Counter, Histogram, REGISTRY, and generate_latest
# come from the Prometheus client library and are used
# to define and export metrics.
from prometheus_client import REGISTRY, Counter, Histogram, generate_latest

# REQUEST_COUNT is a Prometheus counter named http_requests_total.
# It tracks how many HTTP requests have been processed.
# It is labeled by method, path, status_code, and app_env,
# so each combination is tracked separately.
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code", "app_env"],
)

# REQUEST_LATENCY is a histogram named http_request_duration_seconds.
# It records request duration and groups values into latency buckets like 0.05, 0.1, 0.25, etc.
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path", "app_env"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)

# Add db_errors_total metric in myapp
# You will use operation to label which DB call failed (e.g. "get_user", "create_user"), and app_env from APP_ENV
DB_ERRORS_TOTAL = Counter(
    "db_errors_total",
    "Total database errors",
    ["operation", "app_env"],
)

# Python:
# - Python function parameters must be written as name:annotation
# - the middleware factory should return a fully typed callable,
#   and the inner async middleware needs parameter and return
#   annotations.
# - Callable must include both argument and return types,
#   otherwise mypy raises Missing type arguments for
#   generic type "Callable". In this case, _middleware is an async function, so its return type is an awaitable Response, which is why Awaitable[Response] is the right shape.


# metrics_middleware(app_env)
# This function returns an async middleware function
# that wraps each request.
def metrics_middleware(
    app_env: str,
) -> Callable[
    [Request, Callable[[Request], Awaitable[Response]]],
    Awaitable[Response],
]:
    async def _middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # It records the start time with time.perf_counter().
        start = time.perf_counter()
        # It lets the request continue through the app
        # using await call_next(request).
        response: Response = await call_next(request)
        # After the response comes back, it calculates total duration.
        duration = time.perf_counter() - start

        # It reads the request method, path, and response status code.
        path = request.url.path
        method = request.method
        status_code = str(response.status_code)

        # It increments the counter and records the latency for that request.
        # What the data looks like
        # A request like GET /users returning 200 in environment prod would:
        #   - increment http_requests_total{method="GET", path="/users", status_code="200", app_env="prod"}
        #   - add its duration to http_request_duration_seconds{method="GET", path="/users", app_env="prod"}
        # Why this is useful
        # This gives you basic observability:
        #   - request volume,
        #   - response latency,
        #   - breakdown by route, method, status code, and environment.
        # That makes it easy to monitor app health in Prometheus and visualize trends in Grafana.
        REQUEST_COUNT.labels(method, path, status_code, app_env).inc()
        REQUEST_LATENCY.labels(method, path, app_env).observe(duration)

        # It returns the original response unchanged
        return response

    return _middleware


# metrics_endpoint()
# This function exposes all currently registered
# Prometheus metrics.
async def metrics_endpoint() -> Response:
    # Expose all metrics in Prometheus format
    # serializes all collected metrics into Prometheus text format.
    content = generate_latest(REGISTRY)
    # The response content type text/plain; version=0.0.4
    # is the standard format Prometheus expects when scraping
    # metrics endpoints
    return Response(content=content, media_type="text/plain; version=0.0.4")
