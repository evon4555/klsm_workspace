# Package 2026-07-15

Module: Configuration Related

Package date: 2026-07-15

Package type: standard-product requirement evaluation

Current status: current 13-case scope passed; execution review ready

## Source Documents

- `01-input/01-figma/1.png` through `01-input/01-figma/7.png` - UI screenshots for batch session configuration changes.
- `01-input/03-prd/禅道地址.txt` - ZenTao story URL: `https://lengliwh.chandao.net/story-view-4086.html`.
- `01-input/03-prd/story-4086.md` - ZenTao story 4086 exported through the ZenTao API.
- `01-input/03-prd/story-4086.raw.json` - raw ZenTao API response for story 4086.
- `01-input/02-mindmap/` - empty as of 2026-07-15.

## Requirement Summary

This package appears to cover batch configuration changes on the session
management list in the standard-product admin backend.

Confirmed from ZenTao story 4086 and screenshots:

- batch modify session saleable ticket groups
- batch modify whether selected sessions are shown in the session list
- batch modify whether selected sessions are shown in calendar
- common pre-generation preview before final confirmation
- row-level removal from the generated preview before confirming the batch update

The direct `story-view-4086.html` page requires ZenTao login in a browser, but
the story body is readable through the existing workspace ZenTao API token and
has been exported to `01-input/03-prd/story-4086.md`.

## Workflow Status

| Stage | Status | Location | Notes |
|---|---|---|---|
| 01-input | ready | `01-input` | Screenshots, ZenTao URL, and ZenTao story export captured. |
| 02-analysis | signed-off | `02-analysis/requirement-consolidation-batch-session-configuration.md` | Requirement scope signed off by Test Manager on 2026-07-15. |
| 03-test-design | reviewed | `03-test-design/test-cases-batch-session-configuration.md`; `03-test-design/test-cases-batch-session-configuration.xlsx` | Current scope is 13 cases after Test Manager removed `SIT-TC-STD-CONFIG-015` on 2026-07-17 and `SIT-TC-STD-CONFIG-002` on 2026-07-18. Workbook includes an `Audit Trail` sheet for the post sign-off scope adjustments. |
| 04-test-case-review | signed-off / scope adjusted | `04-test-case-review/test-case-review-batch-session-configuration.md`; `04-test-case-review/test-case-review-batch-session-configuration.docx` | Test Manager signed off the English-only v1.1 review package on 2026-07-15; later review trail rows record the 2026-07-17 removal of case 015 and the 2026-07-18 removal of case 002. |
| 05-execution | complete for current scope | `05-execution` | Dashboard run `200` passed all 13 current-scope cases with UI/Mixed screenshots and API transition evidence. No manual case remains after `SIT-TC-STD-CONFIG-015` and `SIT-TC-STD-CONFIG-002` removal. |
| 06-execution-review | drafted | `06-execution-review/execution-review-batch-session-configuration.md`; `06-execution-review/execution-review-batch-session-configuration.docx` | QA readiness recommendation refreshed from the current run `200` execution snapshot. |
| 07-release-feedback | pending | `07-release-feedback` | Reserved for post-release feedback, production issues, accepted risk follow-up, hotfix/rollback notes, and future improvement items. |

## Key Outputs

- `01-input/input-index.md`
- `02-analysis/requirement-consolidation-batch-session-configuration.md`
- `02-analysis/requirement-consolidation-batch-session-configuration.docx`
- `03-test-design/test-cases-batch-session-configuration.md`
- `03-test-design/test-cases-batch-session-configuration.xlsx`
- `03-test-design/.iterations/qa2-self-check-batch-session-configuration.md`
- `03-test-design/.iterations/translation-review-batch-session-configuration-r1.md`
- `03-test-design/CHANGE.md`
- `03-test-design/README.md`
- `04-test-case-review/test-case-review-batch-session-configuration.md`
- `04-test-case-review/test-case-review-batch-session-configuration.docx`
- `05-execution/01-automation-demo/README.md`
- `05-execution/01-automation-demo/short demo.docx`
- `05-execution/01-automation-demo/automation-demo-walkthrough.md`
- `05-execution/01-automation-demo/automation-demo-review-batch-session-configuration.md`
- `05-execution/02-automation-assessment/automation-assessment-batch-session-configuration.md`
- `05-execution/02-automation-assessment/automation-assessment-batch-session-configuration.xlsx`
- `05-execution/02-automation-assessment/automation-assessment-review-batch-session-configuration.md`
- `05-execution/02-automation-assessment/automation-assessment-review-batch-session-configuration.docx`
- `05-execution/03-automation-implementation/api-endpoint-map-batch-session-configuration.md`
- `05-execution/03-automation-implementation/automation-script-implementation-batch-session-configuration.md`
- `05-execution/04-execution-results/execution-results-batch-session-configuration.md`
- `05-execution/04-execution-results/execution-results-batch-session-configuration.json`
- `05-execution/04-execution-results/README.md`
- `05-execution/05-manual-execution/README.md`
- `05-execution/06-defect-triage/README.md`
- `06-execution-review/execution-review-batch-session-configuration.md`
- `06-execution-review/execution-review-batch-session-configuration.docx`
- `D:\Workspace\standard product\02-automation\01-features\README.md`

## Gate

Requirement scope and test-case review are signed off. Test design has been
drafted, translated to English-only wording, exported to the standard-product
workbook template, QA2 self-checked, and approved by Test Manager.

The automation demo walkthrough in `05-execution/01-automation-demo` has been
reviewed against the signed test cases. No missing key business scenario was
found, so no return to `03-test-design` / `04-test-case-review` is required from
this demo review.

The automation assessment review in
`05-execution/02-automation-assessment/automation-assessment-review-batch-session-configuration.docx` was
signed off by the Test Manager on 2026-07-16. QA Automation may proceed with
script implementation from the signed assessment.

The first local pytest/local-fixture implementation has been invalidated and
must not be counted as API/UI/Mixed automation execution.

Valid automation for this package must follow the Behave-first strategy:

- API = Behave + Python `requests` against the real backend API.
- UI = Behave + Playwright against the real application UI.
- Mixed = Behave + real API setup/action, with Playwright only for final UI verification.

Valid Behave execution has now been run for Batch Session Configuration.
Dashboard run `200` for project `standard product` passed all 13 current-scope
cases. API cases generate per-case transition evidence PNG/JSON showing
precondition setup, before value, write request/response, expected value, after
value, and assertion result. Mixed case `SIT-TC-STD-CONFIG-013` now keeps one
API setup/action/readback summary screenshot plus one final Playwright UI
assertion screenshot. Runs `196`, `197`, `198`, `199`, and `200` passed
consecutively after `SIT-TC-STD-CONFIG-002` was removed from current scope.
Runs `190` and `194` remain historical evidence but are superseded: run `190`
did not prove API state transition, and run `194` still included the removed
case 002. `SIT-TC-STD-CONFIG-015` was included in the originally signed
15-case set, then removed from current execution scope by Test Manager decision
on 2026-07-17 because the basic save-failure prompt case is unnecessary for
this package. `SIT-TC-STD-CONFIG-002` was removed on 2026-07-18 because the
no-selection scenario depends on unstable list/filter data and current evidence
is not reliable. The execution phase is complete for the current scope and can
proceed to execution review.

The execution review has been drafted in
`06-execution-review/execution-review-batch-session-configuration.docx` using
the fixed snapshot under `05-execution/04-execution-results` as the review
source.
