# 2026-07-18 Dashboard Evidence And Last-Run Display Rule

Scope: QA Dashboard Scenario Results table and `/api/evidence-status`.

Trigger: skipped single-case reruns (#204/#208) became the latest runtime attempt and exposed two dashboard problems: full-run screenshots could be hidden, and the main table could show confusing rerun run IDs/statuses or stale UTC-naive times.

Decision:
- Runtime evidence status must merge all `case-screenshot-manifest-run-*.json` files by case. A later skipped/no-screenshot rerun must not wipe out the latest usable screenshot evidence from a full run.
- Scenario Results `Last Run` shows the latest attempt time for that case, including single-case reruns, but the main row must not show rerun run IDs or skipped statuses such as `#208 / SKIPPED`.
- Rerun details belong in case History/audit and in the rerun log modal, not in the primary package/full-run result row.
- Dashboard DB timestamps are stored as UTC-naive values. Treat naive `YYYY-MM-DDTHH:mm:ss` API timestamps as UTC, then display them in the browser/local timezone. Explicit timezone timestamps such as `+08:00` should be parsed normally.
- Rerun log state must not be cleared by `isRunning` transitions; only project changes should reset the page-level run/log state.

Verification pattern:
- `SIT-TC-STD-CONFIG-013` can have `latest_runtime_run_id=204`, but `runtime_run_id=200` and `screenshot_count=2`.
- The Test Run page can show a per-case rerun time such as `Jul 18, 8:30 PM` in `Last Run`, but Scenario Results must not contain `#208 / SKIPPED`.
- Run #200's DB `finished_at=2026-07-18T08:22:40` should display as local `Jul 18, 2026, 4:22 PM`, not `8:22 AM`.
