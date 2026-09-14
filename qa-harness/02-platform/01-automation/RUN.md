# Runbook

This file is the practical startup guide for this repository.

## Prerequisites

- Windows machine with this repo checked out locally
- Python venv at `<repo>\02-platform\01-automation\.venv` (see CONTRIBUTING.md)
- Node modules at `<repo>\02-platform\02-dashboard\02-frontend\node_modules` (run `npm install`)
- Grafana installed natively at `D:\grafana\grafana-v10.4.1`
- Prometheus installed natively at `D:\prometheus\prometheus-2.51.0.windows-amd64`
- Loki installed natively at `D:\loki\loki-windows-amd64.exe`

## Startup Order

1. Start Prometheus (Windows native)
2. Start Loki (Windows native)
3. Start Grafana (Windows native)
4. Start FastAPI backend
5. Start Vite frontend
6. Open the dashboard

## 1. Start Prometheus

Double-click `infra\start-prometheus.bat`, or from PowerShell:

```powershell
cd <repo>
.\02-platform\03-infra\start-prometheus.bat
```

Expected port: `9090`

## 2. Start Loki

```powershell
cd <repo>
.\02-platform\03-infra\start-loki.bat
```

Expected port: `3100`

## 3. Start Grafana

```powershell
cd <repo>
.\02-platform\03-infra\start-grafana.bat
```

Expected port: `3000`

## 4. Start FastAPI Backend

```powershell
cd <repo>
.\02-platform\01-automation\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8002
```

Expected port: `8002`

Useful API checks:

```powershell
Invoke-RestMethod http://127.0.0.1:8002/api/features
Invoke-RestMethod http://127.0.0.1:8002/api/perf/services
```

## 5. Start Frontend

```powershell
cd <repo>\02-platform\02-dashboard\02-frontend
npm run dev -- --host 127.0.0.1
```

Expected port: `5174`

Notes:

- Vite proxies `/api` and `/ws` to `http://localhost:8002`
- The frontend depends on the backend already listening on `8002`

## 6. Open the Dashboard

`http://127.0.0.1:5174`

Related URLs:

- Dashboard: `http://127.0.0.1:5174`
- FastAPI backend: `http://127.0.0.1:8002`
- Grafana: `http://127.0.0.1:3000`
- Prometheus: `http://127.0.0.1:9090`
- Loki ready endpoint: `http://127.0.0.1:3100/ready`

## Quick Verification Commands

Check listening ports:

```powershell
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in 3000,3100,9090,8002,5174 } | Sort-Object LocalPort
```

Check backend service status:

```powershell
Invoke-RestMethod http://127.0.0.1:8002/api/perf/services
```

Check observability status:

```powershell
Invoke-RestMethod http://127.0.0.1:8002/api/observability/status
```

## Stop Commands

`Ctrl+C` in each respective terminal: frontend, backend, Grafana, Loki,
Prometheus.

No WSL or Docker steps. The whole stack is Windows-native since 2026-05-27
(see SESSION_NOTES.md).

## Current Service Matrix

| Service | Runtime | Port | Start Method |
| --- | --- | --- | --- |
| Prometheus | Windows native | `9090` | `infra\start-prometheus.bat` |
| Loki | Windows native | `3100` | `infra\start-loki.bat` |
| Grafana | Windows native | `3000` | `infra\start-grafana.bat` |
| FastAPI backend | Windows | `8002` | `uvicorn` |
| Vite frontend | Windows | `5174` | `npm run dev` |
| Locust | Windows (transient) | `9646` | triggered via `/api/perf/run` |
