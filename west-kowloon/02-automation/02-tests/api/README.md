# API Tests

Pytest-based API layers for the West Kowloon Website.

Every completed pytest API session is also published to the local QA
Dashboard (`http://127.0.0.1:8002` by default). It appears in **Test Run** as
an **API run**, with stable API case identifiers, per-case status, and
**Automation Type = API**. Tests under `api_ui_mixed` remain **Mixed** because
they intentionally combine API setup with UI verification. Publishing is
best-effort and never changes the pytest exit result if the dashboard is down.

This folder is intentionally split by test style so the operating model is visible from the directory tree:

```text
02-tests/api\
  api_smoke\       pure single-API monitoring: status code, latency, basic availability
  api_contract\    pure API contract checks: response schema and expected errcode
  api_functional\  pure API functional journeys: multi-step API-only assertions
  api_ui_mixed\    API chain first, then final UI assertion with the same session
  data\            endpoint registry and API test data
  conftest.py      shared fixtures, session handling, JSON sidecar, layer summary
```

## Layer Rules

| Layer | Folder | What It Proves | When To Use |
|---|---|---|---|
| API smoke | `api_smoke/` | A single endpoint is reachable and responds within the expected status/latency envelope. | Scheduled monitoring and quick health checks. |
| API contract | `api_contract/` | The endpoint response keeps the expected JSON shape and success code. | Catch breaking API changes. |
| API functional | `api_functional/` | Multiple API calls agree with each other across a business journey. | Fast deterministic business checks without browser timing risk. |
| API + UI mixed | `api_ui_mixed/` | API creates or verifies the business state, then UI confirms the final user-visible result. | Important user flows where full UI setup is slow or flaky. |

Pure browser E2E scenarios live in `../../01-features/ui_e2e`. Behave API+UI mixed scenarios live in `../../01-features/api_ui_mixed`.
Shared API+UI flow helpers live in `../../03-src/test_automation/flows`.

## Running

```powershell
cd D:\Workspace\west-kowloon\02-automation
$env:ENV = 'sit'

# Layer 1: pure single-API smoke
pytest 02-tests/api/api_smoke -v

# Layer 2: pure API contract
pytest 02-tests/api/api_contract -v

# Layer 3: pure API functional journeys
pytest 02-tests/api/api_functional -v

# Layer 4: API + UI mixed pytest references
pytest 02-tests/api/api_ui_mixed -v

# All API layers
pytest 02-tests/api -v
```

## Artifacts

`api_smoke` writes endpoint details to:

```text
07-artifacts/api_smoke/latest.json
```

`conftest.py` writes per-layer counts to:

```text
07-artifacts/api_smoke/layer_summary.json
```

The dashboard API Monitor reads these files directly.

## Session Refresh

Authenticated API and API+UI mixed tests reuse:

```text
07-artifacts/api_smoke/storage_state.json
```

Refresh the logged-in browser session when needed:

```powershell
python 04-tools/crawl_api_endpoints.py
python 04-tools/crawl_api_endpoints.py --deep
python 04-tools/crawl_api_endpoints.py --force-login
```

The crawler logs in once with Playwright, stores cookies, and the API fixtures reuse the same session until expiry.

## Adding A New Endpoint To API Smoke

1. Edit `data/wk_endpoints.yml`.
2. Add the endpoint under `endpoints:`.
3. Run `pytest 02-tests/api/api_smoke -v`.
4. Refresh the dashboard API Monitor page.

## Adding A Contract Test

1. Define or extend the pydantic model in `api_contract/schemas.py`.
2. Add a target to `CONTRACT_TARGETS`.
3. Run `pytest 02-tests/api/api_contract -v`.

## Adding A Functional API Journey

Add the journey to `api_functional/test_functional.py` when the assertion can be made fully through API responses.

## Adding API + UI Mixed Coverage

Use `api_ui_mixed/` when a check needs both:

- API-shaped assertions: status, body fields, latency, or backend state.
- UI-shaped assertions: visible final state, no redirect, user-facing text.

Reference:

```powershell
D:\Workspace\qa-harness\02-platform\01-automation\.venv\Scripts\python.exe -m pytest 02-tests/api/api_ui_mixed/test_auth009_api_first_ui.py -v -s
```

## CI Note

CI can run `api_smoke` and `api_contract` without secrets when auth-required endpoints are expected to reject anonymous calls. `api_functional` and `api_ui_mixed` may need a fresh `storage_state.json` or configured credentials depending on the scenario.
