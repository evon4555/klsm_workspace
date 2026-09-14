# 02-platform/02-dashboard/02-frontend/

Vite + React 18 + Ant Design + Recharts UI. Runs on `5174`.

## Entry point

```powershell
cd <repo>\02-platform\02-dashboard\02-frontend
npm run dev -- --host 127.0.0.1
```

(`start-all.bat` does this automatically.)

For a single dashboard process, run `npm run build` and then launch the backend,
or use `D:\Workspace\qa-harness\start-dashboard.bat`. FastAPI serves the
generated `dist` bundle on port `8002`.

## Structure

```
src/
├── App.jsx                     React root + routing
├── main.jsx                    Vite entry, mounts App
├── api.js                      Centralized fetch helpers calling /api/*
├── apiClient.js                Shared JSON and HTTP error handling
├── projectContext.js           URL/localStorage project context helpers
├── components/                 Reusable UI bits (badges, status pills, ...)
└── pages/
    ├── TestRunsPage.jsx        Run list + run detail (the home page)
    ├── PerformanceTestPage.jsx Trigger Locust, embed Grafana iframes
    ├── ObservabilityPage.jsx   Loki logs + Pyroscope flame graphs
    └── ... (other module pages)
```

## How it talks to the backend

- `/api/*` requests are proxied to `http://localhost:8002` by `vite.config.js`.
- `/ws/*` WebSocket requests likewise.
- This is dev-mode only; `npm run build` produces a static bundle that can
  be served by FastAPI, any static server, or behind nginx.

## Validation

```powershell
npm run test
npm run build
# or both:
npm run check
```

## Polling cadence

- Most lists auto-refresh every 3 s while their page is open.
- Perf test status: 3 s poll while running.
- Live test log: WebSocket — no polling needed.

## See also

- [`../README.md`](../README.md) — dashboard tier overview
- [`../01-backend/README.md`](../01-backend/README.md) — the API the frontend talks to
- `vite.config.js` — proxy config (port + ws target)
