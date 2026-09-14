# West Kowloon Automation

This folder owns West Kowloon-specific automation assets.

```text
02-automation\
  01-features\    Behave feature files and step definitions
  02-tests\       Pytest API tests and Locust performance tests
  03-src\         Reusable source code imported by tests, steps, and tools
  04-tools\       One-off or operational helper scripts
  05-config\      Project config such as test users
  06-envs\        Environment examples and local env files
  07-artifacts\   Generated run output, logs, screenshots, reports
```

## Placement Rules

Use this rule before adding or moving a file:

| Need | Folder |
|---|---|
| Behave `.feature` scenario or Behave step definition | `01-features` |
| Runnable pytest API test | `02-tests\api` |
| Runnable Locust performance test | `02-tests\performance` |
| Page object, selector model, or reusable browser helper | `03-src\test_automation\web` |
| Reusable API+UI or business flow helper imported by tests/tools | `03-src\test_automation\flows` |
| Delivery helper, evidence writeback, probe, crawler, ZenTao helper, or local diagnostic script | `04-tools` |
| Test users, endpoint registry, non-secret project config | `05-config` or the nearest `data` folder under the test layer |
| Environment file or example | `06-envs` |
| Generated screenshots, JSON, HAR, CSV, browser state, logs, temporary run output | `07-artifacts` |

Do not put runnable tests in `03-src`, and do not put reusable source modules in
`04-tools` unless they are intentionally one-off operational scripts.

Reusable automation framework code stays in:

```text
D:\Workspace\qa-harness\02-platform\01-automation
```

No compatibility junctions are required for normal work. New commands should
use the numbered paths directly.

## Website Test Layers

The current Website automation model is split by test style:

```text
01-features\
  api_ui_mixed\   API chain/setup + final UI assertion through Behave
  ui_e2e\         pure UI / E2E Behave scenarios

02-tests\api\
  api_smoke\       pure single-API smoke checks
  api_contract\    pure API schema / contract checks
  api_functional\  pure API multi-step business checks
  api_ui_mixed\    pytest references for shared-session API + UI checks

03-src\test_automation\
  web\              page objects only
  flows\            reusable API+UI and business flow runners
```

Use the narrowest reliable layer first. API smoke is for health monitoring,
API contract and functional tests are for fast backend confidence, API+UI mixed
is for business chains with a final page assertion, and UI E2E is for full
browser journeys where the user experience itself is the risk.

Ownership rule:

- If a file names West Kowloon, Antank, concrete URLs, concrete accounts,
  project evidence, page objects, steps, delivery scripts, or project-specific
  helper functions, it belongs here.
- If a file is a project-neutral runner, validator, reporting helper, pytest
  plugin, or framework primitive, it belongs in the harness platform.
