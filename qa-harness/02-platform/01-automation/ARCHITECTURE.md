# Architecture

This project combines project-owned test automation, a shared local dashboard,
and several observability services.

## High-Level View

```text
Browser
  ->
Vite Frontend (5174, development)
  ->
FastAPI Backend (8002)
  ->
SQLite + Behave runner + performance artifacts
  ->
Prometheus / Grafana / Loki
```

## Main Components

### Frontend

Location:

`02-platform/02-dashboard/02-frontend`

Technology:

- Vite
- React
- Ant Design

Responsibility:

- Display dashboard pages
- Call backend APIs through `/api`
- Connect to backend WebSocket through `/ws`
- Show run history, trends, flaky tests, performance charts, and observability panels

Important runtime detail:

- Dev server runs on `5174`
- Vite proxies `/api` and `/ws` to `http://localhost:8002`

### Backend

Location:

`02-platform/02-dashboard/01-backend`

Technology:

- FastAPI
- SQLite via SQLAlchemy
- Async background tasks

Responsibility:

- Expose dashboard APIs
- Execute Behave test runs in the background
- Persist runs and scenarios to SQLite
- Query Prometheus, Grafana, and Loki
- Parse Locust CSV artifacts for the performance page

Important files:

- `02-platform/02-dashboard/projects.json`
- `02-platform/02-dashboard/01-backend/main.py`
- `02-platform/02-dashboard/01-backend/project_catalog.py`
- `02-platform/02-dashboard/01-backend/database.py`
- `02-platform/02-dashboard/01-backend/runner.py`
- `02-platform/02-dashboard/01-backend/metrics_client.py`
- `02-platform/02-dashboard/01-backend/dashboard.db`

### Test Assets

Locations under each project workspace:

- `<project>/02-automation/01-features/`
- `<project>/02-automation/02-tests/`
- `<project>/02-automation/07-artifacts/`

Responsibility:

- `features/`: Behave feature definitions
- `tests/`: API, UI, hybrid, and performance tests
- `artifacts/`: generated outputs such as performance CSV data

### Observability Stack

Locations (all under `infra/`):

- `start-prometheus.bat` + `prometheus/prometheus.yml`
- `start-loki.bat` + `loki/loki-config.yaml`
- `start-grafana.bat` + `grafana/grafana.windows.ini` + `grafana/provisioning/`

Components (all Windows-native since 2026-05-27 — see SESSION_NOTES.md):

- Prometheus: metrics collection (`D:\prometheus\prometheus-2.51.0.windows-amd64\`)
- Loki: logs (`D:\loki\loki-windows-amd64.exe`)
- Grafana: dashboards (`D:\grafana\grafana-v10.4.1\`)
- Pyroscope and Toxiproxy: optional integrations checked by the backend

## Data Flow

### Test Run Flow

```text
Frontend
  -> POST /api/runs
Backend
  -> create run record in SQLite
  -> start Behave runner in background
  -> stream logs via /ws/runs/{id}
  -> write final scenario results to SQLite
Frontend
  -> read /api/runs and /api/runs/{id}
```

### Performance Flow

```text
Frontend
  -> POST /api/perf/run
Backend
  -> launch Locust headless process
  -> write CSV files under artifacts/
  -> query Prometheus for live metrics
  -> query Grafana for dashboard/panel URLs
Frontend
  -> render report, charts, and embedded panels
```

### Observability Flow

```text
Frontend
  -> GET /api/perf/services
  -> GET /api/observability/status
Backend
  -> check Prometheus health
  -> check Grafana health
  -> check Loki readiness
  -> return connection status to UI
```

## Port Relationships

| Component | Port | Notes |
| --- | --- | --- |
| Frontend | `5174` | Browser entry point |
| Backend | `8002` | API and WebSocket server |
| Grafana | `3000` | Dashboard UI |
| Loki | `3100` | Log query endpoint |
| Prometheus | `9090` | Metrics API |
| Locust | `9646` | Transient, only during a perf run |

## Environment and Configuration

Project/workspace/ZenTao mappings are owned by
`02-platform/02-dashboard/projects.json`; the frontend does not duplicate them.

The backend loads observability URLs from environment variables, with defaults pointing to localhost:

- `PROMETHEUS_URL`
- `GRAFANA_URL`
- `GRAFANA_API_KEY`
- `GRAFANA_DASHBOARD_UID`
- `LOKI_URL`
- `PYROSCOPE_URL`
- `TOXIPROXY_URL`

If `envs/.env.local` exists, the backend loads values from it at startup.

## Current Implementation Notes

- All three observability services run as Windows-native binaries — no
  Docker, no WSL. Each has its own `.bat` launcher under `infra/`.
- The frontend is configured for backend port `8002`.
- `start-dashboard.bat` builds Vite and lets FastAPI serve the bundle on `8002`;
  `start-all.bat` remains the development/HMR launcher.
- `qa-harness` uses backend/frontend ports `8002/5174`. The original
  `D:\TestAutomation2` dashboard historically used `8001/5173`, so these ports
  can run side by side during migration.

## Practical Mental Model

If you need one simple way to think about the system:

- The frontend is only a UI shell
- The backend is the orchestration layer
- SQLite stores run history
- Behave and Locust generate execution data
- Prometheus/Grafana/Loki provide observability data shown in the dashboard
