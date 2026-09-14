# 2026-07-18 Dashboard Rerun Run-Kind Rule

Scope: QA Dashboard test-run lifecycle under `D:\Workspace\qa-harness\02-platform\02-dashboard`.

Trigger: single-case reruns and "Rerun Failed" were being treated as normal runs, which allowed partial reruns to replace the latest package/full-run summary.

Decision:
- `run_kind=full` is the only run type used for package status, quality gates, trends, KPI cards, and the run selector.
- `run_kind=rerun_single` and `run_kind=rerun_failed` are case-level audit attempts. They update per-case Last Run/history, but must not replace the selected full-run summary.
- Scenario history remains execution-result centric: the timeline shows only Pass/Fail execution results. Skipped/non-execution reruns can affect attempt counts and Last Run metadata, but should not render as Pass/Fail history events.
- Frontend project context is global. Test Run controls must not add a second per-tab project selector/label.

Verification pattern:
- `/api/runs?project=standard product` should return run #200 before run #201 when #201 is a single rerun.
- `/api/runs/200` should keep case 013 status as passed while its Last Run metadata may point to rerun #201 skipped.
- Package linked runs, trends, and quality gates must exclude reruns by default.
