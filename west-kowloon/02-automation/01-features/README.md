# 01-features

Behave feature files for Website UI-facing scenarios.

This folder is split by test style:

```text
01-features\
  api_ui_mixed\   API chains or setup first, final user-visible state asserted on UI
  ui_e2e\         pure UI / E2E browser scenarios
  steps\          shared Behave step definitions
  environment.py  Playwright lifecycle, NA skipping, dashboard sync
```

Use `../02-tests/api/api_smoke` for pure single-API monitoring. Do not put API-only tests here.

## Layers

| Layer | Folder | Purpose |
|---|---|---|
| API + UI mixed | `api_ui_mixed/` | Use API calls for fast setup or business-chain execution, then assert the final page state in the browser. |
| UI E2E | `ui_e2e/` | Drive the user journey through the browser end to end. Use for user-visible flows and long-chain scenarios. |

## Feature Files

| File | Layer | Module | Tags | Covered case IDs |
|---|---|---|---|---|
| `api_ui_mixed/antank_api_first_ui.feature` | API + UI mixed | Registered login identity + final profile UI | `@api_first_ui @auth009 @ui` | AUTH-009 |
| `api_ui_mixed/antank_api_ui_mixed_order.feature` | API + UI mixed | Ticketing create/cancel order + final UI status | `@api_ui_mixed @order_cancel @ticketing @api @ui` | TKT-079 |
| `ui_e2e/antank_registration.feature` | UI E2E | Native registration | `@registration @ui` | AUTH-001-006, 008, 029-030, 042, 044, 045, 057, 065 |
| `ui_e2e/antank_email_login.feature` | UI E2E | Email login | `@login @ui` | AUTH-009-012, 026, 031, 048-050, 077 |
| `ui_e2e/antank_forgot_password.feature` | UI E2E | Forgot password | `@forgot @ui` | AUTH-015, 016, 033, 043, 064, 070 |
| `ui_e2e/antank_guest_login.feature` | UI E2E | Guest login | `@guest @ui` | AUTH-021, 022, 023, 025, 069 |
| `ui_e2e/antank_session_ui.feature` | UI E2E | Session and UI checks | `@session @ui` | AUTH-013, 027, 028 |

## Step Definitions

Step definitions stay shared under `steps/`. The feature subfolder expresses the test style; it does not require separate step packages.

API+UI flow helpers used by steps live under
`../03-src/test_automation/flows`. Page objects used by pure UI steps live under
`../03-src/test_automation/web`.

## Traceability

- Primary key: first whitespace-delimited token in the Scenario name, for example `SIT-TC-WEB-AUTH-009`.
- Optional key: explicit scenario tag, for example `@SIT-TC-WEB-AUTH-009`.
- Validators scan this folder recursively, so both `api_ui_mixed/*.feature` and `ui_e2e/*.feature` are included.

## Running

```powershell
cd D:\Workspace\west-kowloon\02-automation
$env:ENV = 'sit'
$env:PYTHONPATH = 'D:\Workspace\qa-harness\02-platform\01-automation\02-src;D:\Workspace\west-kowloon\02-automation\03-src'

# One UI E2E feature
D:\Workspace\qa-harness\02-platform\01-automation\.venv\Scripts\python.exe -m behave --no-capture 01-features/ui_e2e/antank_email_login.feature --name "SIT-TC-WEB-AUTH-009 "

# One API + UI mixed feature
D:\Workspace\qa-harness\02-platform\01-automation\.venv\Scripts\python.exe -m behave --no-capture 01-features/api_ui_mixed/antank_api_first_ui.feature

# All Behave UI-facing scenarios
D:\Workspace\qa-harness\02-platform\01-automation\.venv\Scripts\python.exe -m behave --no-capture 01-features
```

CLI Behave runs auto-record into `D:\Workspace\qa-harness\02-platform\02-dashboard\01-backend\dashboard.db` through `environment.py`.
