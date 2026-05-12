"""
Unit tests for rate limiter middleware (Phase 4).

Tests the sliding window algorithm and IP extraction without
starting a full ASGI server.
"""

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from api.middleware.rate_limiter import RateLimiterMiddleware


def _make_app(max_requests=3, window_seconds=60):
    """Create a minimal Starlette app with rate limiting."""

    async def homepage(request):
        return PlainTextResponse("ok")

    async def health(request):
        return PlainTextResponse("healthy")

    app = Starlette(
        routes=[
            Route("/api/test", homepage),
            Route("/health", health),
        ]
    )
    app.add_middleware(
        RateLimiterMiddleware,
        max_requests=max_requests,
        window_seconds=window_seconds,
    )
    return app


class TestRateLimiter:
    """Tests for IP-based sliding window rate limiting."""

    def test_requests_within_limit_pass(self):
        app = _make_app(max_requests=5)
        client = TestClient(app)
        for _ in range(5):
            resp = client.get("/api/test")
            assert resp.status_code == 200

    def test_requests_over_limit_get_429(self):
        app = _make_app(max_requests=3)
        client = TestClient(app)
        for _ in range(3):
            resp = client.get("/api/test")
            assert resp.status_code == 200
        # 4th request should be rate limited
        resp = client.get("/api/test")
        assert resp.status_code == 429
        assert "RATE_LIMIT_EXCEEDED" in resp.text

    def test_rate_limit_headers_present(self):
        app = _make_app(max_requests=10)
        client = TestClient(app)
        resp = client.get("/api/test")
        assert "X-RateLimit-Limit" in resp.headers
        assert "X-RateLimit-Remaining" in resp.headers

    def test_remaining_decreases(self):
        app = _make_app(max_requests=5)
        client = TestClient(app)
        r1 = client.get("/api/test")
        r2 = client.get("/api/test")
        rem1 = int(r1.headers["X-RateLimit-Remaining"])
        rem2 = int(r2.headers["X-RateLimit-Remaining"])
        assert rem2 < rem1

    def test_429_includes_retry_after(self):
        app = _make_app(max_requests=1, window_seconds=30)
        client = TestClient(app)
        client.get("/api/test")  # use up limit
        resp = client.get("/api/test")
        assert resp.status_code == 429
        assert "Retry-After" in resp.headers
        assert resp.headers["Retry-After"] == "30"

    def test_health_endpoint_exempt(self):
        app = _make_app(max_requests=1)
        client = TestClient(app)
        client.get("/api/test")  # exhaust limit on /api/test
        # /health should still work
        resp = client.get("/health")
        assert resp.status_code == 200
