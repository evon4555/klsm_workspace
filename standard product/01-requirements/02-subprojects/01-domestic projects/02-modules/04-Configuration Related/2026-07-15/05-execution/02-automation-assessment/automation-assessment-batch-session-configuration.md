# Automation Assessment - Batch Session Configuration

| Item | Value |
|---|---|
| Package | `04-Configuration Related/2026-07-15` |
| Source Test Case Workbook | `../../03-test-design/test-cases-batch-session-configuration.xlsx` |
| Review Workbook | `automation-assessment-batch-session-configuration.xlsx` |
| Current Status | Signed off for automation script implementation; current scope adjusted to 13 cases after `SIT-TC-STD-CONFIG-015` and `SIT-TC-STD-CONFIG-002` removals; post-signoff automation-type correction recorded on 2026-07-17 |
| Workbook Source | `D:\Workspace\standard product\01-requirements\01-source-documents\02-templates\AutomationAssessment_Template.xlsx` |
| Sign-off Source | `automation-assessment-review-batch-session-configuration.docx` |

## Strategy

Use the test pyramid as the default selection rule:

- Prefer API/service-level automation for stable data mutations and validation.
- Use UI automation only for the batch-operation shell, menu availability, mandatory-field guards, and no-save UI behavior.
- Use mixed automation where non-checkpoint setup/action steps should run through real APIs for speed, and only the final user-facing checkpoint is verified with Playwright UI evidence.
- Keep cases manual only when they remain in signed scope and cannot be safely automated.
- Do not assume one reusable service contract across the three UI families. The
  demo shows separate mshow/openShow and seatadmin/schedule endpoint families,
  so each automated main-flow script must confirm the endpoint family and
  persistence readback for its session type and batch action.

## Demo Review

| Item | Decision |
|---|---|
| Demo source | `../01-automation-demo/short demo.docx` |
| Embedded screenshots | 11 usable screenshots reviewed |
| Test-case gap decision | No new key test case required; no return to `03-test-design` / `04-test-case-review` is required. |
| Assessment change | Automation notes updated to treat endpoint mapping as session-family specific, to assert no mutation before confirm for preview deletion / cancel flows, and to record Smoke as scope/priority rather than an implementation layer. |
| Sensitive data handling | Raw cookies, authorization headers, and private payloads from the demo source must not be copied into automation artifacts. |
| Scope adjustment | `SIT-TC-STD-CONFIG-015` was removed from current scope on 2026-07-17 because the basic save-failure prompt case is not necessary for this package. `SIT-TC-STD-CONFIG-002` was removed on 2026-07-18 because the no-selection scenario depends on unstable list/filter data and current evidence is not reliable. |

## Summary

| Metric | Count |
|---|---:|
| Total test cases | 13 |
| Automation = yes | 13 |
| Automation = no | 0 |
| API-led automation | 9 |
| Mixed automation | 1 |
| UI automation | 3 |
| Manual only | 0 |

## Candidate Review

| Case ID | Automation Status | Automation Type | Rationale |
|---|---|---|---|
| SIT-TC-STD-CONFIG-001 | yes | UI | UI smoke coverage. Smoke is the execution scope/priority, but the implementation layer is UI. The demo shows entry/menu selectors differ by UI family, so use resilient selectors and representative data for each family where practical. |
| SIT-TC-STD-CONFIG-003 | yes | API | API-led target; confirm the seat-selection endpoint family and parameter mapping before scripting instead of reusing an mshow/openShow contract by assumption. |
| SIT-TC-STD-CONFIG-004 | yes | API | Demo confirms admission-ticket saleable-group update through the mshow/openShow family using selected session IDs and group ID, with API readback after save. |
| SIT-TC-STD-CONFIG-005 | yes | API | API-led target; confirm the no-seat saleable-group endpoint family and readback path before scripting. |
| SIT-TC-STD-CONFIG-006 | yes | API | API-led target; confirm the seat-selection calendar-display endpoint family and readback path before scripting. |
| SIT-TC-STD-CONFIG-007 | yes | API | API-led target; confirm the admission-ticket calendar-display endpoint family and readback path before scripting. |
| SIT-TC-STD-CONFIG-008 | yes | API | Demo confirms no-seat calendar-display update through the mshow/openShow family using selected session IDs and calendar-display value, with API readback after save. |
| SIT-TC-STD-CONFIG-009 | yes | API | Demo confirms seat-selection session-list display update through the seatadmin/schedule family using selected schedule IDs and display value, with schedule readback after save. |
| SIT-TC-STD-CONFIG-010 | yes | API | API-led target; confirm the admission-ticket session-list display endpoint family and readback path before scripting. |
| SIT-TC-STD-CONFIG-011 | yes | API | API-led target; confirm the no-seat session-list display endpoint family and readback path before scripting. |
| SIT-TC-STD-CONFIG-012 | yes | UI | Implemented as UI mandatory-field validation because the signed scenario verifies a user-facing required-value prompt and no approved safe empty-target API contract is available for this assertion. |
| SIT-TC-STD-CONFIG-013 | yes | Mixed | Use real API for setup/action/readback because the early steps are not the core checkpoint; keep one API summary evidence image, then use Playwright UI for the final user-facing assertion that the remaining row changed and the deleted row stayed unchanged. |
| SIT-TC-STD-CONFIG-014 | yes | UI | Cancel/close remains a UI state-flow check. Assert no mutation endpoint is emitted and API readback shows state unchanged. |
## Review Decision

Automation script implementation may proceed from the signed automation assessment review document. All 13 current-scope cases are selected for automation.
