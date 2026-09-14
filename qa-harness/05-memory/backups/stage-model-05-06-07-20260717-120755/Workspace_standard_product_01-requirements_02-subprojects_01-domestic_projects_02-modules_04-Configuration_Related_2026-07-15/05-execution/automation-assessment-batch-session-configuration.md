# Automation Assessment - Batch Session Configuration

| Item | Value |
|---|---|
| Package | `04-Configuration Related/2026-07-15` |
| Source Test Case Workbook | `../03-test-design/test-cases-batch-session-configuration.xlsx` |
| Review Workbook | `automation-assessment-batch-session-configuration.xlsx` |
| Current Status | Signed off for automation script implementation |
| Template | `D:\Workspace\standard product\01-requirements\01-source-documents\02-templates\AutomationAssessment_Template.xlsx` |
| Sign-off Source | `automation-assessment-review-batch-session-configuration.docx` |

## Strategy

Use the test pyramid as the default selection rule:

- Prefer API/service-level automation for stable data mutations and validation.
- Use UI automation only for the batch-operation shell, menu availability, and no-save UI behavior.
- Use mixed automation where the UI action determines payload shape but API/data checks give reliable assertions.
- Keep cases manual when a controllable test trigger is missing.
- Do not assume one reusable service contract across the three UI families. The
  demo shows separate mshow/openShow and seatadmin/schedule endpoint families,
  so each automated main-flow script must confirm the endpoint family and
  persistence readback for its session type and batch action.

## Demo Review

| Item | Decision |
|---|---|
| Demo source | `01-automation-demo/short demo.docx` |
| Embedded screenshots | 11 usable screenshots reviewed |
| Test-case gap decision | No new key test case required; no return to `03-test-design` / `04-test-case-review` is required. |
| Assessment change | Automation notes updated to treat endpoint mapping as session-family specific and to assert no mutation before confirm for preview deletion / cancel flows. |
| Sensitive data handling | Raw cookies, authorization headers, and private payloads from the demo source must not be copied into automation artifacts. |

## Summary

| Metric | Count |
|---|---:|
| Total test cases | 15 |
| Automation = yes | 14 |
| Automation = no | 1 |
| API-led automation | 10 |
| Mixed automation | 1 |
| UI / Smoke automation | 3 |
| Manual only | 1 |

## Candidate Review

| Case ID | Automation Status | Automation Type | Rationale |
|---|---|---|---|
| SIT-TC-STD-CONFIG-001 | yes | Smoke | Keep as a light UI smoke. The demo shows entry/menu selectors differ by UI family, so use resilient selectors and representative data for each family where practical. |
| SIT-TC-STD-CONFIG-002 | yes | UI | Selection guard is user-facing. Assert that no batch mutation endpoint is emitted when no session is selected. |
| SIT-TC-STD-CONFIG-003 | yes | API | API-led target; confirm the seat-selection endpoint family and parameter mapping before scripting instead of reusing an mshow/openShow contract by assumption. |
| SIT-TC-STD-CONFIG-004 | yes | API | Demo confirms admission-ticket saleable-group update through the mshow/openShow family using selected session IDs and group ID, with API readback after save. |
| SIT-TC-STD-CONFIG-005 | yes | API | API-led target; confirm the no-seat saleable-group endpoint family and readback path before scripting. |
| SIT-TC-STD-CONFIG-006 | yes | API | API-led target; confirm the seat-selection calendar-display endpoint family and readback path before scripting. |
| SIT-TC-STD-CONFIG-007 | yes | API | API-led target; confirm the admission-ticket calendar-display endpoint family and readback path before scripting. |
| SIT-TC-STD-CONFIG-008 | yes | API | Demo confirms no-seat calendar-display update through the mshow/openShow family using selected session IDs and calendar-display value, with API readback after save. |
| SIT-TC-STD-CONFIG-009 | yes | API | Demo confirms seat-selection session-list display update through the seatadmin/schedule family using selected schedule IDs and display value, with schedule readback after save. |
| SIT-TC-STD-CONFIG-010 | yes | API | API-led target; confirm the admission-ticket session-list display endpoint family and readback path before scripting. |
| SIT-TC-STD-CONFIG-011 | yes | API | API-led target; confirm the no-seat session-list display endpoint family and readback path before scripting. |
| SIT-TC-STD-CONFIG-012 | yes | API | Prefer service/API validation when the endpoint safely supports empty or missing target values; otherwise keep a UI-level assertion for the mandatory-field prompt. |
| SIT-TC-STD-CONFIG-013 | yes | Mixed | Demo confirms preview-row deletion should not trigger a save mutation by itself. Use UI to remove the row, assert no mutation before confirm, and assert final payload/readback excludes the deleted row. |
| SIT-TC-STD-CONFIG-014 | yes | UI | Cancel/close remains a UI state-flow check. Assert no mutation endpoint is emitted and API readback shows state unchanged. |
| SIT-TC-STD-CONFIG-015 | no | n/a | Save-failure trigger is not defined; keep manual until Development or Environment Owner provides a controllable failure trigger. |

## Review Decision

Automation script implementation may proceed from the signed automation assessment review document.
