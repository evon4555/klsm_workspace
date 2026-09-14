# 02-platform/02-dashboard/01-backend/

FastAPI app serving the dashboard UI's API + WebSocket. Runs on port `8002`.

## Entry point

`main.py` — composes the FastAPI app, lifecycle, middleware, shared run/evidence
routes, WebSocket logging, and the domain routers under `routers/`. Started for
API/development use by:

```powershell
cd <repo>
.\02-platform\01-automation\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8002
```

(`start-all.bat` does this automatically.)

After the frontend has been built, `start-dashboard.bat` serves both the Vite
bundle and API/WebSocket routes from `http://127.0.0.1:8002`.

## Modules

| File | Purpose |
|---|---|
| `main.py` | FastAPI composition, lifecycle, shared run/evidence routes, and router dependency wiring; loads project env files before runtime clients are created |
| `routers/performance.py` | Locust run control, performance history, metrics, reports, and CSV parsing |
| `routers/observability.py` | Pyroscope, Loki, and Toxiproxy endpoints |
| `routers/api_monitor.py` | API smoke execution state, endpoint results, trends, and layer summaries |
| `routers/zentao.py` | ZenTao products, dashboard, QA task matrix, execution detail, and testcase generation |
| `routers/package_health.py` | Package scanning, drill-down, execution links, promotion, document generation, and xlsx validation |
| `project_catalog.py` | Validated project profiles and project-owned path resolution |
| `frontend_hosting.py` | Vite `dist` static hosting and SPA fallback |
| `database.py` | SQLAlchemy models (`TestRun`, `TestScenario`, `ScenarioBug`) on top of `dashboard.db` |
| `runner.py` | `BehaveRunner` — async subprocess wrapper that launches behave and streams stdout via WebSocket. Sets `BEHAVE_DASHBOARD_RUN_ID` so the env hook doesn't double-record |
| `metrics_client.py` | Async clients for Prometheus / Grafana / Loki / Pyroscope / Toxiproxy; builds the Grafana iframe URLs (`refresh=5s` baked in) |
| `error_analyzer.py` | Heuristic error grouping for the flaky-test view |
| `seed_data.py` | One-time demo data load |
| `dashboard.db` | SQLite file storing all test history; WAL, FK enforcement and indexes are enabled at startup |

## Critical API routes (the ones the frontend depends on)

- `GET  /api/runs` — list test_runs (paginated)
- `GET  /api/runs/{id}` — run detail + scenarios + bugs
- `POST /api/runs` — start a behave run (filtered by feature/tag/scenario)
- `POST /api/runs/{id}/rerun` — rerun the failed scenarios from a run
- `WS   /ws/runs/{id}` — live stdout stream
- `GET  /api/features` — list .feature files + scenarios + tags
- `GET  /api/perf/services` — health of Prometheus / Grafana
- `POST /api/perf/run` — start a Locust test
- `POST /api/perf/stop` — stop the running Locust test (SIGTERM)
- `GET  /api/perf/metrics` — query Prometheus for live perf chart data
- `GET  /api/perf/grafana/panels` — iframe URLs (with `refresh=5s`)
- `GET  /api/perf/report` — parsed Locust CSV from `artifacts/perf_latest_*`
- `GET  /api/history/case/{case_id}` — cross-source history of a single case
- `GET  /api/evidence-status` — xlsx Status + screenshot inventory per case

OpenAPI spec: `http://127.0.0.1:8002/openapi.json`.

`GET /api/health` reports the active DB schema version, project-config version,
and how many stale `running` rows were reconciled at startup.

## Testing layers

Run the backend suite from `01-backend/`:

```powershell
..\..\01-automation\.venv\Scripts\python.exe -m pytest -q tests
```

The `tests/test_domain_api_contracts.py` suite contains Dashboard-internal
application-boundary contract tests. It calls real FastAPI router endpoints via
`TestClient`, while replacing ZenTao, observability services, databases,
subprocesses, and project files with controlled test doubles. These tests
protect HTTP status codes, stable response fields, empty/error states, project
isolation, and secret-free diagnostics.

They are not a replacement for the QA team's product API tests against
Anticket/Antank SIT or UAT. Product API tests validate real business flows,
authentication, data state, integrations, and environment behavior.

For architecture or router changes, the delivery gate is layered: backend
unit/contract tests and route inventory, representative live API calls,
frontend tests and production build, then real-browser smoke across affected
pages and project switching.

## Quirks worth knowing

1. **Env-file loading remains at the top of `main.py`**, before the shared
   runtime clients and domain routers are configured. ENV defaults to `local`.
   Get this wrong and Grafana panels or project runtime settings stay empty.
2. **NaN filtering in `/api/perf/metrics`**: Prometheus returns `"NaN"`
   string for empty rate windows; `float("NaN")` poisons JSON
   serialization. `math.isfinite()` filter is required (see memory
   `feedback_self_smoke_before_done.md` for the audit trail).

## See also

- [`../README.md`](../README.md) — dashboard tier overview + data flow
- [`../../01-automation/CLAUDE.md`](../../01-automation/CLAUDE.md) — service matrix
- [`../../01-automation/TROUBLESHOOTING.md`](../../01-automation/TROUBLESHOOTING.md) — when things break
