# dashboard/

The web dashboard tier of qa-harness. Splits into two processes:

| Process | Stack | Port | Source |
|---|---|---|---|
| **Backend** | FastAPI + SQLAlchemy on top of `dashboard.db` (SQLite) | `8002` | [`01-backend/`](./01-backend/) |
| **Frontend** | Vite + React 18 + Ant Design + Recharts | `5174` | [`02-frontend/`](./02-frontend/) |

The frontend calls the backend via `/api/...` (dev-time Vite proxy) and
`/ws/...` for live test log streaming. The backend reads test history
from `01-backend/dashboard.db`, screenshots from project `<project-root>/02-automation/07-artifacts/`,
and runs `behave` / `locust` as subprocesses.

This dashboard is a QA platform component, not a West Kowloon project artifact.
See [STRATEGY.md](./STRATEGY.md) for the multi-project direction.

## Backend (`01-backend/`)

- `main.py` — FastAPI app, ~30 API routes (incl. `/api/quality-system/*` for Package Health). Lifecycle starts in `init_db()`. Loads `package_scanner` from `01-system/03-tools/` at startup.
- `database.py` — SQLAlchemy models: `TestRun`, `TestScenario`, `ScenarioBug`.
- `metrics_client.py` — async clients for Prometheus / Grafana / Loki / Pyroscope / Toxiproxy.
- `runner.py` — `BehaveRunner` subprocess wrapper; broadcasts log lines via WebSocket.
- `error_analyzer.py` — heuristic error grouping for the flaky-test view.
- `seed_data.py` — initial demo data (used in dev / first-time setup).
- `dashboard.db` — SQLite file; ~100 KB now, will grow with test history.
  Storage limit is set by SQLite (281 TB) but practical limit is well into
  millions of test_scenarios before slowdown.

## Frontend (`02-frontend/`)

- `02-frontend/src/App.jsx` — React root + routing.
- `02-frontend/src/pages/` — per-page React components (test runs, perf test, observability, etc.).
- `02-frontend/src/components/` — reusable UI bits.
- `vite.config.js` — proxies `/api` and `/ws` to `http://localhost:8002`.

## Data flow at a glance

```
behave CLI ── auto-records (env hook) ──► dashboard.db (test_runs / test_scenarios)
                                            ▲
locust ── /metrics on :9646 ──► Prometheus ─┤
                                            │
Backend (FastAPI) ──────────────────────────┴──► reads everything
        │
        ├──► reads project filesystem (01-requirements/) for Package Health
        │
        ▼
Frontend (Vite/React) ── HTTP /api/* ──► Backend
        │
        ▼
Browser (http://127.0.0.1:5174)
```

## Pages

| Page | What it does | Backend endpoints |
|---|---|---|
| Dashboard | KPI cards + recent runs | `/api/runs`, `/api/stats/trends` |
| Test Run | Trigger + watch behave runs | `/api/runs`, `/ws/runs/{id}` |
| QA Decision Center | Per-feature go/no-go view | `/api/quality/evidence`, `/api/history/case/{id}` |
| Email Notification | Test report email config | (config UI only) |
| Performance Test | Locust trigger + metrics | `/api/perf/*` |
| API Monitor | API smoke results + trends | `/api/api-monitor/*` |
| Quality System | Quality-system **build flow** spec — checklists per build phase, role swim-lanes (governance / planning view) | (frontend-only, localStorage) |
| Package Health | Live filesystem scan of every `01-requirements/` package, per-stage status (01-input … 06-release), drill-down, click-to-open file in WPS/Word, run xlsx validator, generate review .docx from .md, show linked dashboard.db runs for the package's case IDs | `/api/quality-system/packages*`, `/api/quality-system/open-file`, `/api/quality-system/generate-docx`, `/api/quality-system/packages/{id}/executions`, `/api/quality-system/packages/{id}/validate-xlsx` |
| ZenTao Integration | Pull stories, generate cases, push back | `/api/zentao/*` |

**Quality System vs Package Health**: two pages, different purposes.
*Quality System* defines what the harness should look like (the spec).
*Package Health* shows what each requirement package actually has on disk
right now (the runtime). The first is for planning, the second is for
day-to-day status. They are deliberately separate — do not merge them.

## Package Health: how it works

The filesystem IS the database. No new DB tables. Every refresh re-walks
`<project>/01-requirements/02-subprojects/*/02-modules/*/<yyyy-mm-dd>/`
and computes per-stage status:

```
Stage           Backed by
01-input        presence of input-index.md + at least one source file
02-analysis     requirement-consolidation-*.md exists; Status field parsed → Signed Off / Awaiting / etc.
03-test-design  test-cases-*.{md,xlsx} present, gated by Step 3.5 (blocked if any consolidation in package isn't Signed Off)
04-test-case-review  matching review form signed, dated, and `Open Review Comments` = None
05-execution    file presence in 05-execution/ (+ on-demand "Show linked runs" JOINs to dashboard.db via xlsx case IDs)
06-release      file presence in 06-release/
```

Per-package case-IDs → dashboard.db join (Phase 2.5):

```
package/03-test-design/**/test-cases-*.xlsx
      └─ Test Case ID column (discovered by header, not fixed index)
           │
           ▼
        set of case IDs (e.g. SIT-TC-WEB-AUTH-001..200)
           │
           ▼
   SELECT * FROM test_scenarios
   WHERE tags LIKE '%<id>%' OR name LIKE '%<id>%'  (one OR per id)
           │
           ▼
   GROUP BY run_id → per-run {scope_matched, scope_passed, scope_failed}
           │
           ▼
   JOIN test_runs for metadata, ORDER BY started_at DESC LIMIT 20
```

The case-prefix scan respects West Kowloon's template (which has a leading
"Label" column pushing "Test Case ID" to column B). The extractor finds the
column by header name, not by fixed position.

Scanner code lives at `01-system/03-tools/package_scanner.py` — runnable
standalone for CLI inspection: `python 01-system/03-tools/package_scanner.py`.

## See also

- [../../README.md](../../README.md) — top-level repo overview
- [../01-automation/CLAUDE.md](../01-automation/CLAUDE.md) — startup commands, service matrix, quirks
- [../01-automation/ARCHITECTURE.md](../01-automation/ARCHITECTURE.md) — component diagram
- [../01-automation/TROUBLESHOOTING.md](../01-automation/TROUBLESHOOTING.md) — common failures
