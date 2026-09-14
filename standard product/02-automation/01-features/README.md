# Standard Product Behave Features

All executable automation in this project must be Behave-first.

Accepted layers:

| Layer | Rule |
|---|---|
| API | Use Python `requests` to call the real backend API. No local service model or mocked contract can count as an API test. |
| UI | Use Playwright against the real application UI. No local HTML fixture can count as a UI test. |
| Mixed | Use API requests for setup and action steps, then use Playwright only for the final UI verification. |

The QA platform reads test-management execution from Behave runs recorded in
`D:\Workspace\qa-harness\02-platform\02-dashboard\01-backend\dashboard.db`.
Pytest-only runs and local fixtures do not satisfy the execution gate.

Tag policy:

| Tag type | Rule |
|---|---|
| Test Case ID | Do not tag case IDs. The full `SIT-TC-...-NNN` ID must stay at the start of the Scenario name and is the canonical mapping key. |
| Scope | Use one suite/module scope tag, for example `@batch_session_configuration`. |
| Automation type | Use exactly one layer tag: `@api`, `@ui`, or `@mixed`. A mixed scenario must not also tag itself as `@api` and `@ui`. |
| Execution guard | Do not add extra technical guard tags to business feature files. Runtime protection is inferred from the scope tag and layer tag in `environment.py`. |

Dashboard display must use signed workbook metadata for Test Case Description
and Automation Type. Raw Behave tags are execution metadata, not user-facing
test result labels.

Smoke coverage is an execution scope or priority decision, not a Behave layer.
The implementation layer should still be recorded as `API`, `UI`, or `Mixed`.
