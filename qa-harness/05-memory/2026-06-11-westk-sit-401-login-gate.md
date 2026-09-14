# 2026-06-11 - WestK SIT Login Gate

Trigger: Running the AUTH-009 API-first UI test with no cached
`storage_state.json`.

Observation: The crawler tried to open `https://anticket.lengliwh.com` and
captured `automation/artifacts/api_smoke/login_error.png` showing nginx
`401 Authorization Required`; Playwright never saw `#login-email`, so pytest
skipped with "no storage_state.json and refresh failed".

Use: Before diagnosing auth test logic, confirm VPN/basic-auth/IP allowlist or
override `WK_API_BASE_URL` to a reachable SIT host, or pre-seed a valid
`automation/artifacts/api_smoke/storage_state.json`.

Dashboard note: When AUTH-009 runs from Behave/dashboard, do not call a helper
that starts `sync_playwright()` again from inside the step. Reuse the
`context.browser` supplied by `features/environment.py` to refresh
`storage_state.json`; otherwise Playwright raises "Sync API inside the asyncio
loop". After this fix, dashboard run #143 reached the real login gate, failed
on `#login-email` timeout, captured the nginx 401 screenshot, and synced TC009
evidence into the xlsx successfully.
