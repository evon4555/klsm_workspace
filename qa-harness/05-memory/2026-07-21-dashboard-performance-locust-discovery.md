# 2026-07-21 Dashboard Performance Locust Discovery

- Trigger: Performance Test failed with `Locust file not found: tests/performance/locustfile.py` after dashboard became multi-project.
- Decision: Performance script selection is project-scoped and API-driven. The frontend must not assume `tests/performance/locustfile.py` exists for every project.
- API rule: `/api/perf/run` must not default `locustfile` to `tests/performance/locustfile.py`; callers must provide a selected file from discovery.
- Applies to: `02-platform/02-dashboard/01-backend/main.py` and `02-platform/02-dashboard/02-frontend/src/pages/PerformanceTestPage.jsx`.
- Expected behavior: no script means warning plus disabled run controls; available scripts are listed from the selected project's `02-automation/02-tests/performance` folder.
