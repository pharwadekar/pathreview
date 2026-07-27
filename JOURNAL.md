# Contribution Journal - PathReview

This journal is a running record of progress on my open source contribution to PathReview.

---

## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The application's health check endpoint in `api/routes/health.py` fails when probing Redis because it attempts to access `settings.redis_host` and `settings.redis_port`, neither of which are defined on the Pydantic `Settings` model in `core/config.py`. Instead, configuration specifies a single `redis_url` connection string. This causes an `AttributeError` that forces the health check to report Redis as unhealthy and return a `503 Service Unavailable` error even when the Redis service is online. A successful fix connects to Redis using `redis.from_url` with `settings.redis_url`, allowing the endpoint to accurately report status.

**Branch name:** fix/155-healthcheck-redis-host

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection Notes & "Is this right for me?" Reasoning:**
* **Scope & Complexity:** The issue is well-scoped to a single API route (`api/routes/health.py`) and configuration file. It does not require database migrations or multi-module alterations, fitting the Tier 1 classification perfectly.
* **Prerequisites:** I verified that Python 3.13 is active, dependencies are installed, and unit tests can be executed locally inside the virtual environment.
* **Testing:** The fix can be cleanly validated using mocks for both successful and failing connection flows, making it highly testable without requiring heavy external dependencies during unit tests.

---

## Week 8 – Reproduction & solution planning

**Reproduction commit link:** https://github.com/pharwadekar/pathreview/commit/cfe95b897130543ecc573264bf01278e6e99fb78

**Reproduction summary:**
Reproduced the issue locally via pytest in `tests/unit/test_health.py`. Running `health_check()` triggers an `AttributeError: 'Settings' object has no attribute 'redis_host'` because `api/routes/health.py` incorrectly attempts to read `settings.redis_host` and `settings.redis_port` instead of using the configured `settings.redis_url` string.

**PLAN.md link:** https://github.com/pharwadekar/pathreview/blob/fix/155-healthcheck-redis-host/PLAN.md

**Walkthrough video (recommended):** N/A (Optional 2-minute walkthrough)

**Blockers or open questions:**
None. Reproduction confirmed via unit tests; solution plan formulated and mapped across API routes and unit test suite.
