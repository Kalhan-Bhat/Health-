"""Hard rule check: the API exposes exactly two application endpoints."""

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import app

EXPECTED_ROUTES = {("POST", "/api/analyze-report"), ("POST", "/api/ask")}


def _collect_api_routes(routes, prefix: str = "") -> set[tuple[str, str]]:
    """Return every (method, path) pair for application routes.

    Older FastAPI versions copy included routes straight into `app.routes` as
    APIRoute objects. Newer versions (0.16x+) keep each included router as a nested
    object with its own prefix, so we walk into those too. Plain Starlette routes
    (the /docs and /openapi.json framework routes) are not APIRoutes and are skipped.
    """
    found: set[tuple[str, str]] = set()
    for route in routes:
        if isinstance(route, APIRoute):
            found |= {(m, prefix + route.path) for m in route.methods}
        elif hasattr(route, "original_router"):  # nested included router (newer FastAPI)
            nested_prefix = prefix + getattr(route.include_context, "prefix", "")
            found |= _collect_api_routes(route.original_router.routes, nested_prefix)
    return found


def test_exactly_two_application_routes() -> None:
    assert _collect_api_routes(app.routes) == EXPECTED_ROUTES


def test_openapi_lists_only_two_paths() -> None:
    # /docs is built from the OpenAPI schema, so this is what /docs shows.
    paths = app.openapi()["paths"]
    assert set(paths) == {"/api/analyze-report", "/api/ask"}
    assert all(set(ops) == {"post"} for ops in paths.values())


def test_other_common_paths_do_not_exist() -> None:
    client = TestClient(app)
    for path in ["/health", "/api/health", "/api/status", "/api/upload", "/api/sources"]:
        res = client.get(path)
        assert res.status_code == 404
        assert res.json()["error"]["code"] == "HTTP_404"


def test_rate_limiter_returns_envelope() -> None:
    """The middleware blocks the request after the limit, with the uniform error shape."""
    from fastapi import FastAPI

    from app.safety.rate_limit import RateLimitMiddleware

    mini = FastAPI()
    mini.add_middleware(RateLimitMiddleware, limit_per_minute=2)

    @mini.post("/api/ping")
    def ping() -> dict:
        return {"ok": True}

    c = TestClient(mini)
    assert [c.post("/api/ping").status_code for _ in range(2)] == [200, 200]
    blocked = c.post("/api/ping")
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "RATE_LIMITED"
    assert "Retry-After" in blocked.headers
