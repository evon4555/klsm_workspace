# 2026-07-20 Performance Run History

- Trigger: A Locust performance test completed from the QA Dashboard, but the user could not see a run record in Dashboard history.
- Decision: Performance runs must create/update `test_runs` with `run_kind="performance"` and write endpoint-level summaries into `test_scenarios`.
- Update: The Performance Test page itself must show script selection and run history. Do not rely on the generic Test Run page as the only visible run record.
- Implementation note: Persist Locust config/aggregate data in `performance_run_configs` so history rows show `host`, `locustfile`, `mode`, `users`, `spawn_rate`, `duration`, requests, failures, error rate, avg response, and RPS.
- Applies to: `02-platform/02-dashboard/01-backend/main.py` performance endpoints and any future Locust/Prometheus/Grafana dashboard integration.
- Verification: `/api/perf/runs?project=west-kowloon` must show performance records, `/api/perf/runs/{id}` must show endpoint rows, and Playwright must verify the Performance Test UI.
