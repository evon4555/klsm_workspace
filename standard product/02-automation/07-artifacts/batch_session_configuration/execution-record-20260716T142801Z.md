# Batch Session Configuration Execution Record

- Suite: `standard_product_batch_session_configuration`
- Requirement package: `04-Configuration Related/2026-07-15`
- Status: `Passed`
- Result: `14 passed / 0 failed / 0 errored / 0 skipped`
- Dashboard run ID: `175`
- Project: `standard product`
- Environment: `sit`
- Started at UTC: `2026-07-16T14:22:27.366163`
- Finished at UTC: `2026-07-16T14:28:01.106930`
- Behave artifact: `D:\Workspace\standard product\02-automation\07-artifacts\batch_session_configuration\latest-full-behave.json`
- Dashboard API check: `http://127.0.0.1:5173/api/runs?project=standard%20product`

## Valid Automation Strategy

This run is valid for QA platform test-management purposes because it uses:

- Behave as the outer scenario runner.
- Python `requests` against real backend APIs for API steps.
- Playwright against the real Standard Product admin UI for UI checks.
- Mixed execution for API setup/action plus final browser-side UI evidence.

## Layer Summary

| Layer | Case IDs | Result |
|---|---|---|
| API | `SIT-TC-STD-CONFIG-003` to `SIT-TC-STD-CONFIG-011` | `9 passed` |
| UI | `SIT-TC-STD-CONFIG-001`, `002`, `012`, `014` | `4 passed` |
| Mixed | `SIT-TC-STD-CONFIG-013` | `1 passed` |

## Case Results

| Case ID | Layer | Status |
|---|---|---|
| `SIT-TC-STD-CONFIG-001` | UI | Passed |
| `SIT-TC-STD-CONFIG-002` | UI | Passed |
| `SIT-TC-STD-CONFIG-003` | API | Passed |
| `SIT-TC-STD-CONFIG-004` | API | Passed |
| `SIT-TC-STD-CONFIG-005` | API | Passed |
| `SIT-TC-STD-CONFIG-006` | API | Passed |
| `SIT-TC-STD-CONFIG-007` | API | Passed |
| `SIT-TC-STD-CONFIG-008` | API | Passed |
| `SIT-TC-STD-CONFIG-009` | API | Passed |
| `SIT-TC-STD-CONFIG-010` | API | Passed |
| `SIT-TC-STD-CONFIG-011` | API | Passed |
| `SIT-TC-STD-CONFIG-012` | UI | Passed |
| `SIT-TC-STD-CONFIG-013` | Mixed | Passed |
| `SIT-TC-STD-CONFIG-014` | UI | Passed |
