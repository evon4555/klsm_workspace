# Execution Results - batch-session-configuration

## Summary

| Item | Value |
| --- | --- |
| Exported At | 2026-07-18T16:22:40+08:00 |
| Dashboard Run | `200` |
| Project | `standard product` |
| Environment | `sit` |
| Run Started | 2026-07-18 08:21:14.103967 |
| Run Finished | 2026-07-18 08:22:40.083541 |
| Result | `13 passed / 0 failed / 0 errored / 0 skipped` |
| Pass Rate | 100.0% |
| Manual Scope | None for current 13-case scope after SIT-TC-STD-CONFIG-002 and SIT-TC-STD-CONFIG-015 removal |

## Trace Links

| Item | Location |
| --- | --- |
| Dashboard Page | http://127.0.0.1:5173/?page=test-run&project=standard%20product |
| Run JSON API | http://127.0.0.1:8002/api/runs/200 |
| SQLite Source | D:/Workspace/qa-harness/02-platform/02-dashboard/01-backend/dashboard.db |
| Artifact Root | D:/Workspace/standard product/02-automation/07-artifacts/batch_session_configuration |
| Runtime Screenshot Manifest | D:/Workspace/standard product/02-automation/07-artifacts/batch_session_configuration/case-screenshot-manifest-run-200.json |
| Test Case Workbook | D:/Workspace/standard product/01-requirements/02-subprojects/01-domestic projects/02-modules/04-Configuration Related/2026-07-15/03-test-design/test-cases-batch-session-configuration.xlsx |
| Automation Assessment Workbook | D:/Workspace/standard product/01-requirements/02-subprojects/01-domestic projects/02-modules/04-Configuration Related/2026-07-15/05-execution/02-automation-assessment/automation-assessment-batch-session-configuration.xlsx |

## Scenario Results

| Case ID | Test Case Description | Automation Type | Status | Duration | Screenshots | Automation Location |
| --- | --- | --- | --- | --- | --- | --- |
| SIT-TC-STD-CONFIG-003 | Verify that seat-selection sessions can be batch-updated to a new saleable ticket group | API | passed | 1.71s | 1 | 01-features/api/batch_session_configuration_api.feature |
| SIT-TC-STD-CONFIG-004 | Verify that admission-ticket sessions can be batch-updated to a new saleable ticket group | API | passed | 1.05s | 1 | 01-features/api/batch_session_configuration_api.feature |
| SIT-TC-STD-CONFIG-005 | Verify that no-seat sessions can be batch-updated to a new saleable ticket group | API | passed | 0.95s | 1 | 01-features/api/batch_session_configuration_api.feature |
| SIT-TC-STD-CONFIG-006 | Verify that seat-selection sessions can be batch-updated for calendar display | API | passed | 1.18s | 1 | 01-features/api/batch_session_configuration_api.feature |
| SIT-TC-STD-CONFIG-007 | Verify that admission-ticket sessions can be batch-updated for calendar display | API | passed | 1.78s | 1 | 01-features/api/batch_session_configuration_api.feature |
| SIT-TC-STD-CONFIG-008 | Verify that no-seat sessions can be batch-updated for calendar display | API | passed | 1.44s | 1 | 01-features/api/batch_session_configuration_api.feature |
| SIT-TC-STD-CONFIG-009 | Verify that seat-selection sessions can be batch-updated for session-list display type | API | passed | 1.36s | 1 | 01-features/api/batch_session_configuration_api.feature |
| SIT-TC-STD-CONFIG-010 | Verify that admission-ticket sessions can be batch-updated for session-list display type | API | passed | 0.69s | 1 | 01-features/api/batch_session_configuration_api.feature |
| SIT-TC-STD-CONFIG-011 | Verify that no-seat sessions can be batch-updated for session-list display type | API | passed | 0.81s | 1 | 01-features/api/batch_session_configuration_api.feature |
| SIT-TC-STD-CONFIG-013 | Verify that deleting a row from the preview excludes that session from submission | Mixed | passed | 13.93s | 2 | 01-features/api_ui_mixed/batch_session_configuration_mixed.feature |
| SIT-TC-STD-CONFIG-001 | Verify that an admin user can open the session batch operation menu after selecting sessions | UI | passed | 12.76s | 2 | 01-features/ui_e2e/batch_session_configuration_ui.feature |
| SIT-TC-STD-CONFIG-012 | Verify that pre-generation is blocked when a required target value is missing | UI | passed | 16.96s | 2 | 01-features/ui_e2e/batch_session_configuration_ui.feature |
| SIT-TC-STD-CONFIG-014 | Verify that canceling or closing the preview does not save changes | UI | passed | 28.34s | 3 | 01-features/ui_e2e/batch_session_configuration_ui.feature |

## Audit Note

- `dashboard.db` is the execution fact source for live dashboard history.
- Runtime screenshot availability is sourced from the per-case screenshot manifest for this run.
- This file is a fixed package-local snapshot for execution review and audit.
- Re-export this document only when a new execution run supersedes the current run.
