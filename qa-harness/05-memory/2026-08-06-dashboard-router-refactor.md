# QA Dashboard Domain Router Refactor

- Date: 2026-08-06
- Trigger: `01-backend/main.py` had grown to 6,306 lines with 53 HTTP routes,
  making domain changes harder to review and isolate.
- Decision: keep the single FastAPI deployment, but move Performance,
  Observability, API Monitor, ZenTao, and Package Health into explicit
  `01-backend/routers/` modules. Public paths and response contracts remain
  unchanged.
- Result: `main.py` is 2,765 lines and retains application composition,
  lifecycle, shared run/evidence behavior, WebSocket logging, and dependency
  wiring. The five router modules own 35 of the 53 HTTP routes.
- Verification: backend `5 passed`; frontend `3 passed`; Vite production build
  passed; documentation smoke `16/16`; representative domain APIs returned
  HTTP 200; browser smoke passed for Test Run, Performance Test, API Monitor,
  Package Health, ZenTao Integration, and project switching.
- Deferred: mutation authentication and Locust path/target allowlisting remain
  intentionally out of scope for the test version. Revisit before shared or
  production deployment.
- Backup: `05-memory/backups/dashboard-router-refactor-20260806-151422`.

## Future Refactor Validation Rule

After any Dashboard architecture or module-boundary refactor, do not stop at a
single unit-test pass. Run multiple validation layers: backend tests and route
inventory, representative live API calls, frontend tests and production build,
then a real browser smoke across affected pages and project switching. Check
browser console and backend logs before declaring the refactor complete.

Dashboard API contract tests are application-boundary tests for the Dashboard
backend itself, not QA product API tests. They use FastAPI `TestClient` with
controlled external dependencies and are a required regression layer for
future router/service refactors.
