# Standard Product Automation

This folder stores automation assets for baseline product behavior.

## Structure

```text
02-automation\
  01-features\
  02-tests\
  03-src\
  04-tools\
  05-config\
  06-envs\
  07-artifacts\
```

Reusable framework code belongs in `D:\Workspace\qa-harness`. Product-specific
automation belongs here.

## Batch Session Configuration

Signed package:
`D:\Workspace\standard product\01-requirements\02-subprojects\01-domestic projects\02-modules\04-Configuration Related\2026-07-15`

Run Batch Session Configuration only after real API endpoint mapping and real
UI flow details are available:

```powershell
.\04-tools\run_batch_session_configuration.ps1
```

Automation strategy:

| Layer | Required implementation |
|---|---|
| API | Behave scenario + Python `requests` calls to the real backend API, plus per-case transition evidence PNG/JSON for write/update cases. |
| UI | Behave scenario + Playwright against the real application UI. |
| Mixed | Behave scenario; all setup/action steps use real API requests, final verification uses Playwright UI. |

The runner sets:

- `QA_PROJECT_AUTOMATION_ROOT` to this `02-automation` folder.
- `PYTHONPATH` to the shared harness source plus this project's `03-src`.

Execution records from valid Behave runs are written to:

`07-artifacts\batch_session_configuration`

QA platform test-management data comes from Behave runs in `dashboard.db`.
Local pytest/local-fixture results must not be reported as API/UI/Mixed
automation execution.

Current fixed execution source: dashboard run `194`, `14 passed / 0 failed /
0 errored / 0 skipped`, with per-case UI/Mixed screenshots and API transition
evidence registered in the runtime screenshot manifest.
