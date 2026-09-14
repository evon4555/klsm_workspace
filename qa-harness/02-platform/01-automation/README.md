# Automation Strategy And Runtime

This subtree contains the reusable automation strategy and runtime for **test
execution**: the Behave + Playwright BDD model, the shared `test_automation`
Python package, platform smoke tools, project onboarding contracts, and
execution runbooks.

The dashboard and observability stack are sibling platform areas under
`D:\Workspace\qa-harness\02-platform`. The harness standards, validators, skills,
and templates live under `D:\Workspace\qa-harness\01-system`.

## Quick Orientation

- All services run on Windows. No WSL, no Docker (since 2026-05-27 — see
  [SESSION_NOTES.md](./SESSION_NOTES.md)).
- Backend on `8002`, frontend on `5174`.
- Grafana on `3000`, Prometheus on `9090`, Loki on `3100`.

If you want to get the project running quickly, start with [RUN.md](./RUN.md).

## Main Docs

- [RUN.md](./RUN.md): startup order, commands, ports, and URLs
- [ARCHITECTURE.md](./ARCHITECTURE.md): how frontend, backend, tests, and observability services fit together
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md): common failures and how to check them
- [CLAUDE.md](./CLAUDE.md): auto-loaded brief for Claude sessions
- [SESSION_NOTES.md](./SESSION_NOTES.md): decision log — why the project looks the way it does
- [strategy/](./01-strategy/): automation strategy, multi-project contract, and project layout

## What's in This Tier

```text
02-platform\01-automation\
  01-strategy\           Multi-project automation strategy and contracts
  02-src\test_automation\ Shared Python package (config, reporting, logging)
  03-tools\              Platform smokes + thin wrappers for project tools
  04-tests\              Generic platform tests
  pyproject.toml         package + optional extras: [web], [app], [dashboard]
  behave.ini
  conftest.py
  .venv\                 local Python environment
```

West Kowloon owns concrete project test assets in numbered project folders:

```text
D:\Workspace\west-kowloon\02-automation\01-features
D:\Workspace\west-kowloon\02-automation\02-tests
D:\Workspace\west-kowloon\02-automation\03-src
D:\Workspace\west-kowloon\02-automation\04-tools
D:\Workspace\west-kowloon\02-automation\05-config
D:\Workspace\west-kowloon\02-automation\06-envs
D:\Workspace\west-kowloon\02-automation\07-artifacts
```

The platform `03-tools` folder may keep thin wrappers for old entry-point names,
but those wrappers delegate to `D:\Workspace\west-kowloon\02-automation\04-tools`.

## Core Ports

| Service | Runs On | Port |
| --- | --- | --- |
| Frontend (Vite) | Windows | `5174` |
| Backend (FastAPI) | Windows | `8002` |
| Grafana | Windows | `3000` |
| Loki | Windows | `3100` |
| Prometheus | Windows | `9090` |
| Locust | Windows (transient) | `9646` |

## Local Dashboard URL

When everything is up: `http://127.0.0.1:5174`

## Environment Notes

The backend auto-loads observability environment variables based on
`ENV` (defaults to `local`):

- `ENV=sit` -> loads `06-envs/.env.sit` when present.
- `ENV=local` -> loads `06-envs/.env.local` when present.
- etc.

Sample: `06-envs/.env.example`. West Kowloon project-specific env files live in
`D:\Workspace\west-kowloon\02-automation\06-envs`.

Important keys for the current West Kowloon fixture:

- `TA_WEBSITE_USERNAME` / `TA_WEBSITE_PASSWORD` (real cred — keep out of git)
- `PROMETHEUS_URL`, `GRAFANA_URL`, `LOKI_URL`
- `PYROSCOPE_URL`, `TOXIPROXY_URL` (optional)

## Recommended Workflow

1. Start Prometheus, Loki, Grafana (each via its `.bat` launcher in `../03-infra/`).
2. Start the FastAPI backend (`uvicorn` from automation/.venv).
3. Start the frontend (`npm run dev` from `../02-dashboard/02-frontend/`).
4. Open the dashboard in the browser at `http://127.0.0.1:5174`.
5. Use the dashboard to inspect runs, trends, logs, and performance data.

Full step-by-step: [RUN.md](./RUN.md).
