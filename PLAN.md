# Solution plan

**Issue:** Health check references `settings.redis_host`, which does not exist on Settings (https://github.com/ascherj/pathreview/issues/155)

### Understand
**Root Cause:**
In `api/routes/health.py`, the Redis probe attempts to connect by reading `settings.redis_host` and `settings.redis_port`:
```python
r = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=0,
    decode_responses=True,
)
```
However, the Pydantic `Settings` model in `core/config.py` only defines a `redis_url` field (`redis://localhost:6379/0`) and does not define `redis_host` or `redis_port`.

**Expected vs. Actual Behavior:**
* **Expected:** The health check endpoint reads `settings.redis_url`, pings the Redis instance, and returns status 200 OK with `"redis": "healthy"` when Redis is reachable (or 503 Service Unavailable when unreachable).
* **Actual:** Accessing `settings.redis_host` raises an `AttributeError` inside the try/except block in `health_check()`. This causes the endpoint to log an error, mark Redis as `unhealthy`, and return HTTP status `503 Service Unavailable` regardless of actual Redis availability.

### Map
The following modules and files are involved:
1. `api/routes/health.py`: Health check API route implementation. (Primary file to modify)
2. `core/config.py`: Application settings defined via Pydantic. (Inspected to verify configuration contract)
3. `tests/unit/test_health.py`: Unit test suite for verifying the health check endpoint response and error handling. (Primary test file)

### Plan
1. **Reproduction & Test Creation:** Create unit tests in `tests/unit/test_health.py` that mock the PostgreSQL database session and simulate both successful and failing Redis ping responses.
2. **Implementation Fix:** Modify `api/routes/health.py` to replace `redis.Redis(host=settings.redis_host, ...)` with `redis.from_url(settings.redis_url, decode_responses=True)`.
3. **Type Annotation & Code Quality Refactoring:** Add precise Python type annotations (`Annotated[AsyncSession, Depends(get_db)]`, return type `dict[str, Any]`, and variable type hints) to ensure compliance with Ruff, Black, and Mypy.
4. **Verification & Quality Checks:** Execute unit tests and run project code quality checks (`ruff`, `black`, `mypy`, and `pytest`) to ensure no regressions or linting failures.

### Inputs & outputs
* **Inputs:** 
  - `settings.redis_url` string (e.g., `"redis://localhost:6379/0"`) from `core/config.py`.
  - HTTP `GET` request to `/health`.
  - `AsyncSession` database dependency via FastAPI dependency injection (`get_db`).
* **Outputs:** 
  - `dict[str, Any]` JSON object with `status`, `dependencies` status map (`postgres`, `redis`, `vector_db`), `safety_events_last_hour`, and UTC timestamp.
  - HTTP Status Code 200 OK when all critical dependencies are healthy.
  - `HTTPException` with status code 503 Service Unavailable when any dependency fails.

### Risks & unknowns
* **Risk 1:** Unexpected network exceptions or timeout during `redis.from_url` instantiation or `ping()` call.
  - *Mitigation:* Ensure `redis.from_url` and `ping()` remain enclosed within a dedicated `try...except Exception as exc` block that logs the exception via `structlog` and sets `health_status["dependencies"]["redis"] = "unhealthy"`.
* **Risk 2:** Mypy type-checking failures due to dynamic Redis client return types or missing FastAPI type parameters.
  - *Mitigation:* Explicitly type-annotate `health_check` and local dictionaries (`dict[str, Any]`), and run `.venv/Scripts/mypy` during local validation.

### Edge cases
1. **Redis Server Connection Refused/Offline:** `r.ping()` raises `redis.exceptions.ConnectionError`. The `try...except` block catches this, marks `"redis": "unhealthy"` and `"status": "unhealthy"`, and raises 503.
2. **Invalid Redis Connection URL Format:** Malformed `settings.redis_url` string causes `redis.from_url` to raise a `ValueError` or `ConfigurationError`. Caught by `except Exception`, handled gracefully with HTTP 503.
3. **PostgreSQL Offline, Redis Online:** Postgres check fails first, but Redis check still executes. Overall status is `"unhealthy"`, returning HTTP 503 with exact dependency statuses (`postgres`: unhealthy, `redis`: healthy).
