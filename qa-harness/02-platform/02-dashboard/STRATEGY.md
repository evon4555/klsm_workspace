# QA Dashboard Strategy

The dashboard is a platform component, not a West Kowloon project artifact.

It exists to make QA strategy observable:

- execution history
- traceability status
- evidence readiness
- defect opening and follow-up
- performance and observability signals
- project quality trend

## Ownership

The dashboard belongs under:

```text
D:\Workspace\qa-harness\02-platform\02-dashboard
```

Projects provide data and adapters. The dashboard should read project data
through project profiles rather than hard-coding a single project.

## Current State

The dashboard still has West Kowloon defaults because it was born from that
project. Those defaults are allowed only as the first smoke fixture. New project
support should be added through configuration, not by copying dashboard code
into a project workspace.

## Platform V1 Project Context

The platform uses a single global project context at dashboard entry:

- `GET /api/projects` returns the known workspace projects and their ZenTao
  defaults.
- The frontend asks for the project once on first entry, then stores the
  selected project in the URL and localStorage.
- All tabs receive the same `activeProject` from `App.jsx`; pages must not add
  independent project switchers. Page-level filters such as ZenTao product can
  remain as second-level filters inside the selected project.
- Test Run, Dashboard trends, flaky detection, API Monitor, Quality System,
  Package Health, QA Decision Center, Performance locustfile discovery, and
  ZenTao QA task matrix are scoped by the selected project.
- Package Health reads the selected project and scans that project's
  `01-requirements` tree.
- ZenTao Integration uses the selected project's default product id as the page
  starting point, while keeping manual product selection available. The QA task
  matrix uses the selected project's mapped default execution.
- Existing dashboard run rows without a project are backfilled as
  `west-kowloon`.

Known project mappings:

| Project | Workspace | Type | ZenTao Product | Default Execution |
|---|---|---|---:|---:|
| West Kowloon | `west-kowloon` | customer | 146 | 614 |
| Standard Product | `standard product` | baseline | 22 | 640 |
| Jockey Club | `jockey club` | customer | - | - |

Implemented platform foundation:

- Project metadata now lives in visible `projects.json`; the frontend obtains
  mappings from `/api/projects` and keeps only a minimal offline fallback.
- Project-aware automation, evidence, screenshot, and Gherkin paths are
  resolved through the backend project catalog.
- Built Vite assets can be hosted by FastAPI for a single dashboard process.

Next platform layer:

- Add lifecycle links from ZenTao story/execution to QA package stage, signed
  gates, automation plan, execution evidence, defect status, and report.
- Replace any remaining environment-level observability assumptions with
  explicit project tags once Prometheus/Loki/Grafana expose project labels.
- Performance, Observability, API Monitor, ZenTao, and Package Health now live
  in domain routers. Extract the remaining run/evidence blocks only when future
  changes justify it; keep the local modular-monolith deployment model.
