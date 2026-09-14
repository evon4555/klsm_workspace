# Test Cases — Batch Session Operation Configuration

| Item | Value |
|----|----|
| Package | `04-Configuration Related/2026-07-15` |
| Scope | `batch-session-configuration` |
| Requirement Basis | `../02-analysis/requirement-consolidation-batch-session-configuration.md` |
| Current Status | Test Manager signed off; automation assessment moved to `../05-execution` |
| Number of Test Cases | 15 |
| Output Note | Markdown source and `test-cases-batch-session-configuration.xlsx` have been generated from the standard-product workbook template. |

## Revision History

| Date | Author | Change | Status |
|----|----|----|----|
| 2026-07-15 | QA1 (AI) | Generated the initial test case set from the signed requirement consolidation. | Completed |
| 2026-07-15 | QA1 (AI) | Generated the xlsx workbook from `02-templates\TestCase_Template.xlsx`. | Completed |
| 2026-07-15 | QA2 Self-check (AI) | Reduced execution granularity: kept the Q-5 main-flow matrix and consolidated shared preview, mandatory-field, exit, and failure checks into shared or data-driven cases. | Completed |
| 2026-07-15 | QA1 (AI) | Applied Test Manager review comment to translate the test case set into English and regenerated the xlsx workbook. | Completed |

## 1. Scope Summary

### 1.1 Signed Decisions

| Decision | Signed Answer | Impact on Test Cases |
|----|----|----|
| Q-1 | a | Cover only the three batch operations explicitly listed in story 4086: saleable ticket group, session-list display, and calendar display. |
| Q-2 | a | Deleting a row from the preview means that session is removed from the current submission. |
| Q-3 | a | Do not include downstream customer-facing purchase or calendar smoke regression in this package. |
| Q-4 | a | Cover only the basic failure prompt; do not cover the full partial-success or rollback matrix. |
| Q-5 | b | Cover the full matrix of three session types by three batch actions. |

### 1.2 Test Granularity

- Keep nine main-flow matrix cases for `three session types × three batch actions` to satisfy Q-5.
- Treat preview row deletion, cancel / close behavior, mandatory-field validation, and save failure as shared component behavior instead of repeating them by every session type and action.
- Use data-driven coverage for low-difference checks to avoid unnecessary execution cost.

### 1.3 In Scope

- Batch operation entry from the admin session management list.
- Batch modification of session saleable ticket groups.
- Batch modification of whether sessions are displayed on the calendar.
- Batch modification of whether sessions are displayed in the session list.
- Pre-generation preview with before / after values.
- Preview row deletion, cancel / close, confirm modification, and callback display after saving.
- Basic failure prompt visibility.

### 1.4 Out of Scope

- Other actions in the batch operation menu.
- API transaction and rollback matrix.
- Permission matrix.
- Customer-facing purchase flow, calendar entry, and frontend display smoke regression.
- Operation log and audit record verification.

## 2. Test Data Assumptions

| Data Item | Requirement |
|----|----|
| Seat-selection sessions | At least two editable sessions whose configuration can be safely modified in the test environment. |
| Admission-ticket sessions | At least two editable sessions whose configuration can be safely modified in the test environment. |
| No-seat sessions | At least two editable sessions whose configuration can be safely modified in the test environment. |
| Saleable ticket groups | At least two searchable and selectable ticket groups; one is used as the target group. |
| Calendar display value | Both `Yes` and `No` can be selected. |
| Session-list display type | `Always display`, `Display until expiry`, and `Do not display` can be selected. |
| Admin user | The user has session management and batch modification permissions. |

## 3. Test Case List

| Case ID | Title | Priority | Coverage Type | Traceability | Preconditions | Test Data | Test Steps | Expected Result | Evidence | Status |
|----|----|----|----|----|----|----|----|----|----|----|
| SIT-TC-STD-CONFIG-001 | Verify that an admin user can open the session batch operation menu after selecting sessions | P1 | Main flow | F1 / Q-1 | The admin user is logged in and has opened the session management list. | Any two editable sessions | 1. Select two sessions in the session management list.<br>2. Click `Session Batch Operations`. | 1. The batch operation menu is displayed.<br>2. The menu contains the three in-scope actions from story 4086.<br>3. No save action is triggered on the current page. | Yes | Not Run |
| SIT-TC-STD-CONFIG-002 | Verify that batch operations cannot be started when no session is selected | P2 | Negative scenario | F1 | The admin user is logged in and has opened the session management list. | No session is selected. | 1. Keep the session list with no selected session.<br>2. Click or try to open `Session Batch Operations`. | 1. The system does not allow the batch operation flow to start, or it shows a prompt requiring the user to select sessions first.<br>2. No preview is generated.<br>3. No configuration is saved. | Yes | Not Run |
| SIT-TC-STD-CONFIG-003 | Verify that seat-selection sessions can be batch-updated to a new saleable ticket group | P1 | Main flow | F2 / F5 / F6 / Q-5 | Two seat-selection sessions and a target ticket group are available. | Session type: seat-selection; action: saleable ticket group | 1. Select two seat-selection sessions.<br>2. Select `Batch Modify Session Saleable Ticket Group`.<br>3. Search for and select the target ticket group.<br>4. Click `Pre-generate`.<br>5. Click `Confirm Modification`.<br>6. Refresh the list or reopen the session detail page. | 1. The setting dialog shows the selected seat-selection sessions and their current saleable ticket groups.<br>2. The preview page shows the original value and the modified value.<br>3. After confirmation, the selected sessions are saved with the target ticket group.<br>4. The list or detail page displays the latest configuration. | Yes | Not Run |
| SIT-TC-STD-CONFIG-004 | Verify that admission-ticket sessions can be batch-updated to a new saleable ticket group | P1 | Main flow | F2 / F5 / F6 / Q-5 | Two admission-ticket sessions and a target ticket group are available. | Session type: admission-ticket; action: saleable ticket group | 1. Select two admission-ticket sessions.<br>2. Select `Batch Modify Session Saleable Ticket Group`.<br>3. Search for and select the target ticket group.<br>4. Click `Pre-generate`.<br>5. Click `Confirm Modification`.<br>6. Refresh the list or reopen the session detail page. | 1. The setting dialog shows the selected admission-ticket sessions and their current saleable ticket groups.<br>2. The preview page shows the original value and the modified value.<br>3. After confirmation, the selected sessions are saved with the target ticket group.<br>4. The list or detail page displays the latest configuration. | Yes | Not Run |
| SIT-TC-STD-CONFIG-005 | Verify that no-seat sessions can be batch-updated to a new saleable ticket group | P1 | Main flow | F2 / F5 / F6 / Q-5 | Two no-seat sessions and a target ticket group are available. | Session type: no-seat; action: saleable ticket group | 1. Select two no-seat sessions.<br>2. Select `Batch Modify Session Saleable Ticket Group`.<br>3. Search for and select the target ticket group.<br>4. Click `Pre-generate`.<br>5. Click `Confirm Modification`.<br>6. Refresh the list or reopen the session detail page. | 1. The setting dialog shows the selected no-seat sessions and their current saleable ticket groups.<br>2. The preview page shows the original value and the modified value.<br>3. After confirmation, the selected sessions are saved with the target ticket group.<br>4. The list or detail page displays the latest configuration. | Yes | Not Run |
| SIT-TC-STD-CONFIG-006 | Verify that seat-selection sessions can be batch-updated for calendar display | P1 | Main flow | F3 / F5 / F6 / Q-5 | Two seat-selection sessions are available. | Session type: seat-selection; action: calendar display | 1. Select two seat-selection sessions.<br>2. Select `Batch Modify Calendar Display`.<br>3. Select the target value.<br>4. Click `Pre-generate`.<br>5. Click `Confirm Modification`.<br>6. Refresh the list or reopen the session detail page. | 1. The setting dialog shows the selected sessions and their current calendar display value.<br>2. The preview page shows the original value and the modified value.<br>3. After confirmation, the selected sessions are saved with the target calendar display value.<br>4. The list or detail page displays the latest configuration. | Yes | Not Run |
| SIT-TC-STD-CONFIG-007 | Verify that admission-ticket sessions can be batch-updated for calendar display | P1 | Main flow | F3 / F5 / F6 / Q-5 | Two admission-ticket sessions are available. | Session type: admission-ticket; action: calendar display | 1. Select two admission-ticket sessions.<br>2. Select `Batch Modify Calendar Display`.<br>3. Select the target value.<br>4. Click `Pre-generate`.<br>5. Click `Confirm Modification`.<br>6. Refresh the list or reopen the session detail page. | 1. The setting dialog shows the selected sessions and their current calendar display value.<br>2. The preview page shows the original value and the modified value.<br>3. After confirmation, the selected sessions are saved with the target calendar display value.<br>4. The list or detail page displays the latest configuration. | Yes | Not Run |
| SIT-TC-STD-CONFIG-008 | Verify that no-seat sessions can be batch-updated for calendar display | P1 | Main flow | F3 / F5 / F6 / Q-5 | Two no-seat sessions are available. | Session type: no-seat; action: calendar display | 1. Select two no-seat sessions.<br>2. Select `Batch Modify Calendar Display`.<br>3. Select the target value.<br>4. Click `Pre-generate`.<br>5. Click `Confirm Modification`.<br>6. Refresh the list or reopen the session detail page. | 1. The setting dialog shows the selected sessions and their current calendar display value.<br>2. The preview page shows the original value and the modified value.<br>3. After confirmation, the selected sessions are saved with the target calendar display value.<br>4. The list or detail page displays the latest configuration. | Yes | Not Run |
| SIT-TC-STD-CONFIG-009 | Verify that seat-selection sessions can be batch-updated for session-list display type | P1 | Main flow | F4 / F5 / F6 / Q-5 | Two seat-selection sessions are available. | Session type: seat-selection; action: session-list display | 1. Select two seat-selection sessions.<br>2. Select the batch action for session-list display.<br>3. Select the target display type.<br>4. Click `Pre-generate`.<br>5. Click `Confirm Modification`.<br>6. Refresh the list or reopen the session detail page. | 1. The setting dialog shows the selected sessions and their current display type.<br>2. The preview page shows the original value and the modified value.<br>3. After confirmation, the selected sessions are saved with the target display type.<br>4. The list or detail page displays the latest configuration. | Yes | Not Run |
| SIT-TC-STD-CONFIG-010 | Verify that admission-ticket sessions can be batch-updated for session-list display type | P1 | Main flow | F4 / F5 / F6 / Q-5 | Two admission-ticket sessions are available. | Session type: admission-ticket; action: session-list display | 1. Select two admission-ticket sessions.<br>2. Select the batch action for session-list display.<br>3. Select the target display type.<br>4. Click `Pre-generate`.<br>5. Click `Confirm Modification`.<br>6. Refresh the list or reopen the session detail page. | 1. The setting dialog shows the selected sessions and their current display type.<br>2. The preview page shows the original value and the modified value.<br>3. After confirmation, the selected sessions are saved with the target display type.<br>4. The list or detail page displays the latest configuration. | Yes | Not Run |
| SIT-TC-STD-CONFIG-011 | Verify that no-seat sessions can be batch-updated for session-list display type | P1 | Main flow | F4 / F5 / F6 / Q-5 | Two no-seat sessions are available. | Session type: no-seat; action: session-list display | 1. Select two no-seat sessions.<br>2. Select the batch action for session-list display.<br>3. Select the target display type.<br>4. Click `Pre-generate`.<br>5. Click `Confirm Modification`.<br>6. Refresh the list or reopen the session detail page. | 1. The setting dialog shows the selected sessions and their current display type.<br>2. The preview page shows the original value and the modified value.<br>3. After confirmation, the selected sessions are saved with the target display type.<br>4. The list or detail page displays the latest configuration. | Yes | Not Run |
| SIT-TC-STD-CONFIG-012 | Verify that pre-generation is blocked when a required target value is missing | P2 | Negative scenario | F2 / F3 / F4 / U-1 | The admin user has selected at least one session and can open the batch modification dialog. | Data set A: no new ticket group is selected for saleable ticket group modification; data set B: neither `Yes` nor `No` is selected for calendar display; data set C: no display type is selected for session-list display. | 1. Open the batch modification dialog for each data set.<br>2. Keep the target value empty.<br>3. Click `Pre-generate`. | 1. The system blocks the preview or shows a mandatory-field prompt.<br>2. No modification preview is generated.<br>3. No configuration is saved. | Yes | Not Run |
| SIT-TC-STD-CONFIG-013 | Verify that deleting a row from the preview excludes that session from submission | P1 | Alternative flow | F5 / Q-2 | An in-scope batch modification preview has been generated with at least two rows. | Any session type; any in-scope batch action | 1. Delete one row from the preview page.<br>2. Click `Confirm Modification`.<br>3. Refresh the list or reopen the session detail page. | 1. The session represented by the deleted row keeps its original configuration.<br>2. Sessions that remain in the preview are saved with the new configuration.<br>3. The deleted row is not included in the submission. | Yes | Not Run |
| SIT-TC-STD-CONFIG-014 | Verify that canceling or closing the preview does not save changes | P1 | Alternative flow | F5 / U-2 | An in-scope batch modification preview has been generated. | Exit methods: cancel, close dialog; any in-scope batch action | 1. Generate a modification preview.<br>2. Click `Cancel`.<br>3. Refresh the list or reopen the session detail page.<br>4. Generate the same type of modification preview again.<br>5. Click the close icon or use the dialog close entry.<br>6. Refresh the list or reopen the session detail page. | 1. The dialog closes after both exit methods.<br>2. The selected sessions keep their original configuration.<br>3. No save result is produced. | Yes | Not Run |
| SIT-TC-STD-CONFIG-015 | Verify that a basic error prompt is displayed when batch saving fails | P2 | Error handling | F6 / Q-4 | The test environment can trigger a save failure or use controlled exception data. | Any session type; any in-scope batch action | 1. Enter the batch modification flow.<br>2. Select data that causes save failure or triggers a controlled exception.<br>3. Click `Confirm Modification`. | 1. The system displays a save-failure prompt.<br>2. The user remains in the current flow or can return to a retryable state.<br>3. Full rollback-matrix verification is not required. | Yes | Not Run |

## 4. Coverage Notes

| Coverage Item | Status | Notes |
|----|----|----|
| Three batch actions | Covered | Saleable ticket group, calendar display, and session-list display are covered by main flows and shared preview / exception behavior. |
| Three session types | Covered | Q-5 selected option `b`; the main flow keeps the nine-case matrix for seat-selection, admission-ticket, and no-seat sessions across the three batch actions. |
| Pre-generation preview | Covered | Main flows cover original and modified values; SIT-TC-STD-CONFIG-013 covers preview row deletion. |
| Cancel / close without saving | Covered | SIT-TC-STD-CONFIG-014 covers shared exit behavior. |
| Mandatory-field validation | Covered | SIT-TC-STD-CONFIG-012 covers three data groups. |
| Callback display after save | Covered | All main-flow cases require the list or detail page to display the latest configuration. |
| Basic failure prompt | Covered | SIT-TC-STD-CONFIG-015 covers the basic failure prompt according to Q-4. |
| Customer-facing smoke regression | Not in scope | Q-3 selected option `a`; this package does not include customer-facing smoke regression. |
| Operation log / audit record | Not in scope | U-5 confirmed that this package does not include audit verification. |
| Permission matrix | Deferred | The requirement consolidation keeps this outside the package; it should be handled by a later permission-configuration package. |

## 5. Review Points

| ID | Question | Impact | Recommendation |
|----|----|----|----|
| R-1 | The save-failure trigger method has not been provided. | SIT-TC-STD-CONFIG-015 may require test-environment support. | Development or Environment Owner should provide a controllable failure trigger before execution. |
