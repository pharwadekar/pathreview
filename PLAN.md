# Solution Plan - Health Check Redis AttributeError (#155)

This document outlines the plan for reproducing, fixing, and verifying the issue where the health check endpoint raises an `AttributeError` due to referencing a non-existent `settings.redis_host` property.

## 1. Issue Reference
* **GitHub Issue:** [pathreview/issues/155](https://github.com/ascherj/pathreview/issues/155)
* **Description:** `api/routes/health.py` reads `settings.redis_host` for its Redis probe, but the `Settings` model does not define that field, so the endpoint raises `AttributeError` before it can report Redis status.

## 2. Problem Analysis & Root Cause
In `core/config.py`, the application settings are defined under the `Settings` Pydantic class:
* It includes a `redis_url` string field (`redis://localhost:6379/0`), but does not define individual `redis_host` or `redis_port` fields.

In `api/routes/health.py`, the Redis check attempts to initialize `redis.Redis` using:
```python
        r = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=0,
            decode_responses=True,
        )
```
This causes an `AttributeError` at runtime, meaning the health check endpoint constantly fails and marks Redis as `unhealthy`, returning a `503 Service Unavailable` status code.

## 3. Reproduction Step
We created a unit test in `tests/unit/test_health.py` that mocks the database but leaves Redis settings intact:
```bash
.venv/Scripts/pytest tests/unit/test_health.py -v
```
Running this test on the original codebase successfully reproduces the error, as the `AttributeError` is raised internally, causing a `503` exception response.

## 4. Proposed Solution
1. **Connect via URL:** Modify `api/routes/health.py` to use `redis.from_url()` using the existing `settings.redis_url` field:
   ```python
   r = redis.from_url(
       settings.redis_url,
       decode_responses=True,
   )
   ```
2. **Type Annotations & Quality:** Update the route parameters and internal variables to use standard typing annotations (e.g. `Annotated[AsyncSession, Depends(get_db)]` and `health_status: dict[str, Any]`), resolving all Ruff, Black, and Mypy warnings.
3. **Unit Tests:** Write robust unit tests verifying both success (Redis ping succeeds) and failure (Redis raises an exception) flows.

## 5. Verification Plan
* **Unit Tests:** Run `.venv/Scripts/pytest tests/unit/test_health.py -v`.
* **Linting & Formatting:** Run Ruff and Black checks:
  ```bash
  .venv/Scripts/ruff check api/routes/health.py tests/unit/test_health.py
  .venv/Scripts/black --check api/routes/health.py tests/unit/test_health.py
  ```
* **Type-Checking:** Run Mypy:
  ```bash
  .venv/Scripts/mypy api/routes/health.py tests/unit/test_health.py --python-version 3.13
  ```
