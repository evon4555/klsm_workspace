# Automation Script Implementation - Batch Session Configuration

| Item | Value |
|---|---|
| Package | `04-Configuration Related/2026-07-15` |
| Signed Assessment Review | `../02-automation-assessment/automation-assessment-review-batch-session-configuration.docx` |
| Script Layer | Behave-first API / UI / Mixed |
| Implementation Status | Implemented and verified |
| Latest Dashboard Run | `194` |
| Latest Result | `14 passed / 0 failed / 0 errored / 0 skipped` |
| Latest Behave Artifact | `D:\Workspace\standard product\02-automation\07-artifacts\batch_session_configuration\latest-full-behave.json` |

## Scope

The signed automation assessment and 2026-07-17 scope adjustment leave 14
current-scope cases, all selected as automatable:

- `SIT-TC-STD-CONFIG-001` to `SIT-TC-STD-CONFIG-014`

`SIT-TC-STD-CONFIG-015` was removed from current scope by Test Manager decision
on 2026-07-17; no automation or manual execution is required for that case in
this package.

## Implemented Layer Split

| Layer | Case IDs | Count | Implementation Rule |
|---|---|---:|---|
| API | `SIT-TC-STD-CONFIG-003` to `SIT-TC-STD-CONFIG-011` | 9 | Behave steps call real backend APIs through Python `requests`. |
| UI | `SIT-TC-STD-CONFIG-001`, `002`, `012`, `014` | 4 | Behave steps drive the real Standard Product admin UI with Playwright. |
| Mixed | `SIT-TC-STD-CONFIG-013` | 1 | Behave uses real API setup/action and browser-side UI evidence for final verification. |

## Current Valid Files

| Purpose | Location |
|---|---|
| API feature | `D:\Workspace\standard product\02-automation\01-features\api\batch_session_configuration_api.feature` |
| UI feature | `D:\Workspace\standard product\02-automation\01-features\ui_e2e\batch_session_configuration_ui.feature` |
| Mixed feature | `D:\Workspace\standard product\02-automation\01-features\api_ui_mixed\batch_session_configuration_mixed.feature` |
| API steps | `D:\Workspace\standard product\02-automation\01-features\steps\batch_session_configuration_api_steps.py` |
| UI/Mixed steps | `D:\Workspace\standard product\02-automation\01-features\steps\batch_session_configuration_ui_steps.py` |
| Behave dashboard hook | `D:\Workspace\standard product\02-automation\01-features\environment.py` |
| API client and flow mapping | `D:\Workspace\standard product\02-automation\03-src\test_automation\standard_product\batch_session_api.py` |
| Admin auth/session | `D:\Workspace\standard product\02-automation\03-src\test_automation\standard_product\admin_auth.py` |
| Admin UI helper | `D:\Workspace\standard product\02-automation\03-src\test_automation\standard_product\admin_ui.py` |
| Runner guard | `D:\Workspace\standard product\02-automation\04-tools\run_batch_session_configuration.ps1` |

## Execution Evidence

| Artifact | Location |
|---|---|
| Latest execution status | `D:\Workspace\standard product\02-automation\07-artifacts\batch_session_configuration\latest-execution-record.md` |
| Latest execution JSON | `D:\Workspace\standard product\02-automation\07-artifacts\batch_session_configuration\latest-execution-record.json` |
| Latest Behave JSON | `D:\Workspace\standard product\02-automation\07-artifacts\batch_session_configuration\latest-full-behave.json` |
| Layer summary | `D:\Workspace\standard product\02-automation\07-artifacts\batch_session_configuration\layer_summary.json` |
| Runtime case evidence | `D:\Workspace\standard product\02-automation\07-artifacts\batch_session_configuration\run-194\...\*.png`; API cases also write paired `*.json` evidence |

## Dashboard Verification

QA dashboard API returned the latest Standard Product run:

```text
GET http://127.0.0.1:8002/api/runs/194
run id: 194
project: standard product
env: sit
status: passed
total: 14
passed: 14
failed: 0
errored: 0
skipped: 0
```

## Run Command Used

The run reads credentials from the local Standard Product access reference at
execution time. Secrets are not written into the scripts or evidence files.

```powershell
cd 'D:\Workspace\standard product\02-automation'

$accessPath = 'D:\Workspace\standard product\01-requirements\02-subprojects\01-domestic projects\01-source-documents\网站地址以及权限.txt'
$access = Get-Content -Raw -LiteralPath $accessPath
$m = [regex]::Match($access, 'Mplus01\s*/\s*([^\s]+)')

$env:ENV='sit'
$env:TA_ENV='sit'
$env:TA_ANTANK_URL='https://anticket.lengliwh.com'
$env:TA_BASE_URL='https://anticket.lengliwh.com'
$env:TA_USER1_USERNAME='Mplus01'
$env:TA_USER1_PASSWORD=$m.Groups[1].Value
$env:TA_ALLOW_BATCH_MUTATION='1'
$env:QA_PROJECT_KEY='standard product'
$env:QA_PROJECT_AUTOMATION_ROOT='D:\Workspace\standard product\02-automation'
$env:PYTHONPATH='D:\Workspace\qa-harness\02-platform\01-automation\02-src;D:\Workspace\standard product\02-automation\03-src'

D:\Workspace\qa-harness\02-platform\01-automation\.venv\Scripts\python.exe -m behave `
  'D:\Workspace\standard product\02-automation\01-features' `
  --tags='@batch_session_configuration' `
  --format json `
  --outfile 'D:\Workspace\standard product\02-automation\07-artifacts\batch_session_configuration\latest-full-behave.json' `
  --format pretty `
  --no-capture
```

## Stabilization Notes

- The Standard Product run is written with `project_key='standard product'`.
- API and Mixed steps reuse one real `requests.Session` per Behave run to avoid repeated CAPTCHA/OCR login failures while still sending real API requests.
- UI steps seed Playwright browser cookies from the real API session when available, then keep request capture enabled for no-write assertions.
- The UI helper waits for the business SPA to expose the query controls before interacting.
- The UI helper retries mshow route recovery and rechecks expected no-seat rows before treating a with-rows schedule page as ready.
- Batch menu selection only clicks visible menu/action candidates, avoiding stale hidden drawer DOM.
- `SIT-TC-STD-CONFIG-014` resets the no-seat session page between the return-preview and close-preview subflows so the two checks remain independent.
- Runs `183`, `184`, `185`, `186`, and `187` all passed `14/14` after stabilization. Run `190` passed `14/14` after API readback evidence was added but is superseded because it did not prove a state transition for write/update cases. Run `194` passed `14/14` with transition evidence and is the current fixed execution-review source.
- API write/update cases generate per-case evidence PNG/JSON only after the precondition value differs from the target, the write API is accepted, and post-write readback shows the field changed to the expected value.
