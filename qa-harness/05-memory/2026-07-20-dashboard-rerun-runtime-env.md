# 2026-07-20 Dashboard Rerun Runtime Env Rule

Trigger: Standard Product Dashboard rerun created run rows but Behave scenarios were skipped or errored because the backend runner did not load the project runtime context used by the project PowerShell runner.

Decision: Dashboard-launched Behave runs must build project-scoped runtime environment before launching the child process. The runner must set `QA_PROJECT_KEY`, `QA_PROJECT_AUTOMATION_ROOT`, `QA_WORKSPACE_ROOT`, `QA_HARNESS_ROOT`, load project `06-envs/.env.<env>`, and use runtime-only local access-file lookup when a project already documents that handoff. Do not log, store, or copy secrets.

Applies: `02-platform/02-dashboard/01-backend/runner.py`, `main.py`, and all project automation roots under `D:\Workspace\<project>\02-automation`.

Required behavior:
- `Rerun Failed` selects both failed and errored scenarios.
- Runs with `total > 0` and zero executed scenarios are error/blocked, not passed.
- WebSocket clients that connect after a fast run finishes must receive existing logs and a done signal.
- Scenario Results should show latest executable attempt status while preserving selected full-run status in tooltip/history for audit.

Verification from the fix:
- Row rerun `#214`: `SIT-TC-STD-CONFIG-013`, `1 executed / 1 passed / 0 skipped`.
- Failed/errored rerun `#215`: `3 executed / 3 passed / 0 skipped`.
- Full run `#217`: `13 executed / 13 passed / 0 skipped`.
