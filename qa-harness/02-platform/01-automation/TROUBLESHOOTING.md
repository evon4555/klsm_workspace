# Troubleshooting

This file lists the most common local failures for this project and the quickest checks.

## First Checks

When the dashboard does not work, check these first:

1. Is the frontend listening on `5174`?
2. Is the backend listening on `8002`?
3. Is Grafana listening on `3000` (via `infra\start-grafana.bat`)?
4. Is Prometheus listening on `9090` (via `infra\start-prometheus.bat`)?
5. Is Loki listening on `3100` (via `infra\start-loki.bat`)?
6. Is the frontend trying to reach the backend on the correct port?

Useful command:

```powershell
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in 3000,3100,9090,8002,5174 } | Sort-Object LocalPort
```

## Frontend Does Not Open

Symptom:

- `http://127.0.0.1:5174` does not load

Check:

```powershell
cd <repo>\02-platform\02-dashboard\02-frontend
npm run dev -- --host 127.0.0.1
```

If it fails:

- make sure `node_modules` exists (`npm install` from the same dir)
- make sure no other process is already using `5174`

Check port owner:

```powershell
Get-NetTCPConnection -LocalPort 5174 -State Listen -ErrorAction SilentlyContinue
```

## Frontend Loads but API Calls Fail

Symptom:

- UI opens but data is empty
- pages show network errors

Check backend:

```powershell
Invoke-RestMethod http://127.0.0.1:8002/api/features
```

If backend is not up, start it:

```powershell
cd <repo>
.\02-platform\01-automation\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8002
```

Important:

- Vite proxy is configured to use backend port `8002`
- If you start the backend on a different port, edit `02-platform/02-dashboard/02-frontend/vite.config.js`

## Backend Starts but Dashboard Shows Services Disconnected

Check:

```powershell
Invoke-RestMethod http://127.0.0.1:8002/api/perf/services
Invoke-RestMethod http://127.0.0.1:8002/api/observability/status
```

Expected connected services in the current setup:

- Prometheus
- Grafana
- Loki

Optional and often disconnected unless you explicitly run them:

- Pyroscope
- Toxiproxy

## Prometheus / Loki / Grafana Not Running

All three are Windows-native binaries (since 2026-05-27 — see SESSION_NOTES.md).
Each has its own `.bat` launcher; start them individually:

```powershell
cd <repo>
.\02-platform\03-infra\start-prometheus.bat
.\02-platform\03-infra\start-loki.bat
.\02-platform\03-infra\start-grafana.bat
```

Direct health checks:

```powershell
Invoke-WebRequest http://127.0.0.1:9090/-/healthy -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:3000/api/health -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:3100/ready -UseBasicParsing
```

If a launcher fails: confirm the install dir exists. Prometheus expects
`D:\prometheus\prometheus-2.51.0.windows-amd64\`, Loki expects
`D:\loki\loki-windows-amd64.exe`, Grafana expects `D:\grafana\grafana-v10.4.1\`.
See CONTRIBUTING.md for download URLs.

## Port Already In Use

Check a specific port:

```powershell
Get-NetTCPConnection -State Listen -LocalPort 8002 -ErrorAction SilentlyContinue
```

Map PID to process:

```powershell
Get-Process -Id <PID>
```

Common ports in this project:

- `5174` frontend
- `8002` backend
- `3000` Grafana
- `3100` Loki
- `9090` Prometheus
- `9646` Locust (transient, only during a perf run)

## Backend Imports or Python Environment Problems

Check that the project virtual environment exists at
`<repo>\02-platform\01-automation\.venv` and that `test_automation` imports from
qa-harness:

```powershell
.\02-platform\01-automation\.venv\Scripts\python.exe -c "import test_automation; print(test_automation.__file__)"
# Expected: <repo>\02-platform\01-automation\02-src\test_automation\__init__.py
```

If packages are missing or the import path is wrong:

```powershell
cd <repo>\automation
.\.venv\Scripts\python.exe -m pip install -e ".[web,dashboard]"
```

## Dashboard Page Opens but Looks Partially Broken

Current known harmless issue:

- missing `favicon.ico` may show one `404` in the browser console

This does not block dashboard usage.

## Useful One-Shot Health Script

```powershell
Invoke-RestMethod http://127.0.0.1:8002/api/perf/services
Invoke-RestMethod http://127.0.0.1:8002/api/observability/status
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in 3000,3100,9090,8002,5174 } | Sort-Object LocalPort
```

## When You Need to Rebuild Local State

Least invasive restart order:

1. Stop frontend
2. Stop backend
3. Stop Grafana / Loki / Prometheus (Ctrl+C in each window)
4. Start Prometheus, Loki, Grafana (in that order)
5. Start backend again
6. Start frontend again

Each is a single .bat or single PowerShell command — see RUN.md for the
exact invocations.
