## Summary
This pull request fixes a runtime `AttributeError` in the `/health` API endpoint (`api/routes/health.py`). Previously, the Redis health check probe attempted to read `settings.redis_host` and `settings.redis_port` attributes on the Pydantic `Settings` instance. Because `core/config.py` only defines a single `redis_url` string field, accessing `redis_host` raised an `AttributeError` inside the try/except block. This caused the health check endpoint to always mark Redis as `unhealthy` and return HTTP status `503 Service Unavailable` regardless of actual Redis server health. 

This PR refactors the Redis probe to initialize connection via `redis.from_url(settings.redis_url, decode_responses=True)`, accurately probing Redis health and returning HTTP 200 OK when Redis is healthy or HTTP 503 when unreachable.

## Issue
Closes #155 (https://github.com/ascherj/pathreview/issues/155)

## Changes
- **Refactored Redis Health Check Probe:** Modified `api/routes/health.py` to instantiate the Redis client using `redis.from_url(settings.redis_url, decode_responses=True)` instead of `redis.Redis(host=settings.redis_host, port=settings.redis_port, ...)`.
- **Enhanced Type Annotations:** Updated FastAPI route dependency parameters to use `Annotated[AsyncSession, Depends(get_db)]` and return type `dict[str, Any]` to meet project typing standards.
- **Added Unit Test Coverage:** Created `tests/unit/test_health.py` with test cases `test_health_check_all_healthy` (verifies 200 OK status when PostgreSQL and Redis pass) and `test_health_check_redis_unhealthy` (verifies 503 Service Unavailable status when Redis connection fails).
- **Code Quality Compliance:** Validated formatting, linting, and type annotations against Ruff, Black, and Mypy.

## Testing
### Manual & Automated Verification Instructions
1. Activate the Python 3.13 virtual environment and run the health check unit tests:
   ```bash
   .\.venv\Scripts\pytest.exe tests/unit/test_health.py -v
   ```
   *Expected Result:* Both `test_health_check_all_healthy` and `test_health_check_redis_unhealthy` pass cleanly in < 1 second.
2. Run code style and linting checks:
   ```bash
   .\.venv\Scripts\ruff.exe check api/routes/health.py tests/unit/test_health.py
   .\.venv\Scripts\black.exe --check api/routes/health.py tests/unit/test_health.py
   ```
   *Expected Result:* All checks pass with 0 errors.
3. Run static type checker:
   ```bash
   .\.venv\Scripts\mypy.exe api/routes/health.py tests/unit/test_health.py --python-version 3.13
   ```
   *Expected Result:* `Success: no issues found in 2 source files`.

### Pre-Submission Checklist
- [x] Unit tests pass (`make test-unit`)
- [x] Integration tests pass (`make test-integration`)
- [x] Linter passes (`make lint`)
- [x] Type checker passes (`make typecheck`)
- [x] New/updated tests cover the changes

## Screenshots / Demo
Pytest test run log output:
```text
tests/unit/test_health.py::test_health_check_all_healthy PASSED          [ 50%]
tests/unit/test_health.py::test_health_check_redis_unhealthy PASSED      [100%]
======================== 2 passed in 0.83s ========================
```

## Notes for Reviewers
- The change is strictly scoped to `api/routes/health.py` and `tests/unit/test_health.py`.
- No configuration additions or database migrations are required, as `redis_url` was already defined in `core/config.py`.
- Error handling continues to log via `structlog` and properly catch network/connection exceptions.
