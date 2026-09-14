# 02-platform/02-dashboard/01-backend/

FastAPI app serving the dashboard UI's API + WebSocket. Runs on port `8002`.

## Entry point

`main.py` — defines the FastAPI app, 50+ API/WebSocket routes, and lifecycle
setup. Started for API/development use by:

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
| `main.py` | FastAPI app + routes; loads `automation/envs/.env.<ENV>` at import |
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

## Quirks worth knowing

1. **Env-file loader is at the top of `main.py`** (before any route reads
   `os.environ.get("GRAFANA_DASHBOARD_UID", ...)`). Path is
   `repo_root / "automation" / "envs" / f".env.{ENV}"`. ENV defaults to
   `local`. Get this wrong and Grafana panels stay empty.
2. **NaN filtering in `/api/perf/metrics`**: Prometheus returns `"NaN"`
   string for empty rate windows; `float("NaN")` poisons JSON
   serialization. `math.isfinite()` filter is required (see memory
   `feedback_self_smoke_before_done.md` for the audit trail).

## See also

- [`../README.md`](../README.md) — dashboard tier overview + data flow
- [`../../01-automation/CLAUDE.md`](../../01-automation/CLAUDE.md) — service matrix
- [`../../01-automation/TROUBLESHOOTING.md`](../../01-automation/TROUBLESHOOTING.md) — when things break
