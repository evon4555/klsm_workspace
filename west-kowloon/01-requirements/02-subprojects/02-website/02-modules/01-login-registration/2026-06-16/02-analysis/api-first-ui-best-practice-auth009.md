# API-First UI Best Practice: AUTH-009

Date: 2026-06-11

Chosen scenario: `SIT-TC-WEB-AUTH-009 Registered user logs in via email and password`.

## Principle

API owns the workflow. UI validates only the final user-visible state.

For this project, password login is protected by an image captcha. The harness
therefore uses the existing Playwright crawler only to bootstrap a valid
`storage_state.json`. After that point, the test treats API as the driver:
the same cookie jar is loaded into `requests.Session` for API assertions and
into Playwright for final UI acceptance.

## Flow

1. `authed_http` loads or refreshes the logged-in session.
2. `POST /ucenter/rest/getLogonInfo.xhtml` confirms the current login identity.
3. `GET /thvendor/member/info/getMemberInfo.xhtml` confirms the member service
   agrees with the login service on member id and email.
4. `GET /thvendor/member/info/getPersonalInfo.xhtml` confirms the profile API
   accepts the same session.
5. Playwright opens `/websitehtml/index.html#/my/profile` with the same
   `storage_state.json`.
6. UI passes only if it is not redirected to `#/login` and the profile page
   exposes the same email returned by the API.

## Automation

Executable reference:

`D:\Workspace\west-kowloon\02-automation\02-tests\api\api_ui_mixed\test_auth009_api_first_ui.py`

Run:

```powershell
cd D:\Workspace\west-kowloon\02-automation
$env:ENV = "sit"
D:\Workspace\qa-harness\02-platform\01-automation\.venv\Scripts\python.exe -m pytest 02-tests/api/api_ui_mixed/test_auth009_api_first_ui.py -v -s
```

Evidence output, created by the test run:

D:\Workspace\west-kowloon\02-automation\07-artifacts\api_first_ui\

## Dashboard Validation

Dashboard scope:

`API-first UI (1)`

Dashboard labels:

- Scope selected: `API-first UI (1)`
- Run button: `Run: API-first UI`
- Sync button: `Sync -> xlsx: API-first UI`
- Scenario tags: `api_first_ui`, `auth009`, `SIT-TC-WEB-AUTH-009`

Latest dashboard run on 2026-06-11:

- Run: `#143`
- Result: `failed` at the SIT login gate, not at the dashboard chain
- Root evidence folder: `D:\Workspace\west-kowloon\02-automation\07-artifacts\api_smoke\`
- Dashboard logs folder: `D:\Workspace\qa-harness\02-platform\02-dashboard\logs\`
- Xlsx sync: succeeded for `SIT-TC-WEB-AUTH-009`
- Workbook: `D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\01-login-registration\2026-06-16\03-test-design\test-cases-registration-login.xlsx`
- Embedded evidence strip: `D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\01-login-registration\2026-06-16\05-execution\evidence\registration-TC009-fail-2026-06-11.png`

If the run skips with `no storage_state.json and refresh failed`, check the
login screenshot at:

`D:\Workspace\west-kowloon\02-automation\07-artifacts\api_smoke\01_login_page_opened.png`

On 2026-06-11 this local machine reached nginx `401 Authorization Required`
instead of the login form, so Playwright never found `#login-email`. Fix the
environment gate first: VPN/basic-auth/IP allowlist, `WK_API_BASE_URL`, or a
pre-seeded valid `storage_state.json`.

## When To Use This Pattern

Use it when the main risk is backend state, identity, permissions, or data
consistency, and the UI only needs to prove the final user-facing state.

Do not use it when the main risk is field-level interaction, visual layout,
accessibility, copy, captcha behavior, button state, or browser-only routing.
Those still belong in focused UI tests.

## Copy Template

For another login or registration case, keep this split:

- API setup: create or locate the required account/session state.
- API assertions: verify every service boundary that owns the business truth.
- UI final check: open the final page with the same session and assert only
  the user-visible contract.
- Evidence: save one UI screenshot plus API response metadata, never secrets.
