# Claude Notes — qa-harness automation tier

This file is auto-loaded by Claude. Keep brief. Deeper procedures live in
[RUN.md](./RUN.md), [TROUBLESHOOTING.md](./TROUBLESHOOTING.md),
[ARCHITECTURE.md](./ARCHITECTURE.md), [SESSION_NOTES.md](./SESSION_NOTES.md).

## What this project is

Reusable QA automation strategy and runtime. Stack: FastAPI backend + Vite/React
frontend + Behave tests + Locust load testing + Prometheus/Grafana/Loki
observability. **100% Windows-native** since 2026-05-27 (WSL Docker retired
— see SESSION_NOTES.md "Migrate observability to Windows native").

Current default smoke fixture is West Kowloon. Project-specific features, page
objects, performance scripts, and delivery tools live in
`D:\Workspace\west-kowloon\02-automation`.

## When user asks "start QA dashboard"

Run all 5 steps. Verify between steps. Most start commands need
`run_in_background=true` since they are long-running.

| # | Service | Command |
|---|---|---|
| 1 | Prometheus (Windows native) | from repo root: `infra\start-prometheus.bat` in background |
| 2 | Loki (Windows native) | from repo root: `infra\start-loki.bat` in background |
| 3 | Grafana (Windows native) | from repo root: `infra\start-grafana.bat` in background |
| 4 | FastAPI backend | from repo root: `.\02-platform\01-automation\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8002` in background |
| 5 | Vite frontend | from `dashboard\frontend`: `npm run dev -- --host 127.0.0.1` in background |
| 6 | Verify | check ports 3000/3100/5174/8002/9090 listening; `curl http://127.0.0.1:8002/api/perf/services` returns prometheus+grafana connected |

Open `http://127.0.0.1:5174` when all green.

## When user asks "stop QA dashboard"

Ctrl+C / TaskStop frontend, backend, Grafana, Loki, Prometheus (each in its
own window). No WSL / Docker steps needed anymore.

## Pass-row refresh policy (since 2026-05-27)

**Do NOT auto-run `tools/update_evidence.py` or any other bulk job that
overwrites xlsx Status for already-Pass scenarios.** On an actively-developed
product, transient network / OCR / product-UI changes flip Pass to Fail and
create noise. Manual refresh from the dashboard UI is always OK.

When asked to "refresh results", default to running ONLY rows currently
marked Fail or NA. See memory `feedback_dont_refresh_pass_scenarios.md`.

## Self-smoke before reporting "done" (since 2026-05-28)

**After ANY change to `02-platform/02-dashboard/01-backend/`, `02-platform/02-dashboard/02-frontend/src/`,
`02-automation/03-src/test_automation/web/`, `02-automation/01-features/environment.py`,
`02-platform/03-infra/`, or `automation/envs/.env.*` — run the smoke script and paste
output:**

```powershell
cd <repo>
.\02-platform\01-automation\.venv\Scripts\python.exe 02-platform\01-automation\03-tools\smoke_dashboard.py
```

Runtime ~90 s. Exit 0 = all 28 checks PASS; non-zero = something to fix
before claiming done. The script exercises every link in the data flow
(ports → backend routes → frontend proxy → behave dashboard-sync → full
perf chain Locust→Prometheus→Grafana). Catches the bug classes that bit
the user 2026-05-27 (NaN crash, stuck Grafana iframes, IPv6 scrape
mismatch, env-loading path regression). See memory
`feedback_self_smoke_before_done.md`.

## Key quirks — do NOT forget

1. **Everything runs on Windows now.** Prometheus + Loki are Windows-native
   binaries at `D:\prometheus\prometheus-2.51.0.windows-amd64\` and
   `D:\loki\loki-windows-amd64.exe`. Versions match the previous Docker
   images (Prom 2.51.0, Loki 2.9.6). Their data lives outside the repo at
   `D:\prometheus\data\` and `D:\loki\data\`.

2. **Locust scrape target** is `localhost:9646` directly (no more
   `host.docker.internal` indirection). Locust still only listens when a
   perf test is active.

3. **Grafana shows data only while Locust runs.** Locust exposes metrics on
   `:9646` only when a test is active. Trigger via
   `POST http://127.0.0.1:8002/api/perf/run` with body
   `{"host":"<project-perf-host>","users":5,"spawn_rate":1,"duration":"60s"}`
   for a quick sanity test. The current default fixture uses West Kowloon.

4. **Grafana login** is `admin / admin` (also has anonymous Viewer enabled).
   Dashboard: `http://127.0.0.1:3000/d/locust-perf`.

5. **Backend on 8002, frontend on 5174.** Historically these were 8001/5173
   in the legacy D:\TestAutomation2 stack; qa-harness uses 8002/5174 to keep
   port assignments stable after the migration finished (TA2 was retired
   2026-05-29). The ports can be reassigned freely now that the original is
   gone — preserved here for ops continuity.

## Service matrix

| Service | Runtime | Port | Start |
|---|---|---|---|
| Prometheus | Windows native | 9090 | `infra\start-prometheus.bat` |
| Loki | Windows native | 3100 | `infra\start-loki.bat` |
| Grafana | Windows native | 3000 | `infra\start-grafana.bat` |
| FastAPI backend | Windows | 8002 | `uvicorn` from automation venv |
| Vite frontend | Windows | 5174 | `npm run dev` from 02-platform/02-dashboard/02-frontend |
| Locust | Windows (transient) | 9646 | triggered via `/api/perf/run` |

## Useful one-shot verifications

```powershell
# All ports listening
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in 3000,3100,9090,8002,5174 } | Sort-Object LocalPort

# Backend health
Invoke-RestMethod http://127.0.0.1:8002/api/perf/services

# Prometheus targets (Locust will be DOWN unless a perf test is running)
curl -s http://127.0.0.1:9090/api/v1/targets | python -c "import sys,json; [print(t['labels']['job'], t['health']) for t in json.load(sys.stdin)['data']['activeTargets']]"

# Loki readiness
curl http://127.0.0.1:3100/ready

# Grafana → Prometheus through proxy (should be HTTP 200)
curl -s -u admin:admin -o /dev/null -w "%{http_code}" "http://127.0.0.1:3000/api/datasources/proxy/uid/PBFA97CFB590B2093/api/v1/query?query=up"
```

## When in doubt

- Startup procedure: [RUN.md](./RUN.md)
- Specific failure: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- "Why did we do X": [SESSION_NOTES.md](./SESSION_NOTES.md)
- Component layout: [ARCHITECTURE.md](./ARCHITECTURE.md)
