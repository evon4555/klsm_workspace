# Standard Product Review and Test Templates

This folder is the authoritative template location for standard-product
requirement and QA deliverables.

| Template | Required Use |
|---|---|
| `TestCase_Template.xlsx` | Authoritative workbook schema for generated test cases. Clone this file and swap in data; do not rebuild workbooks from scratch. |
| `TestCase_Template_pre-label.xlsx` | Legacy 19-column workbook schema before the `Label` column. Keep as a reference; do not use unless explicitly requested. |
| `AutomationAssessment_Template.xlsx` | Authoritative workbook schema for automation assessment after the automation-demo review gate. Clone this file and fill case-level automation decisions; do not put sign-off fields in this workbook. |
| `Requirement Review Template.docx` | Mandatory v2.1 human-facing requirement review / scope sign-off template for future `02-analysis/requirement-consolidation-<scope>.docx` handoffs. |
| `Requirement Review Template.md` | Canonical content source for the requirement review template. |
| `Test Case Review Template.docx` | Mandatory v2.1 human-facing Test Manager sign-off template for future `04-test-case-review/test-case-review-<scope>.docx` handoffs. |
| `Test Case Review Template.md` | Canonical content source for the test-case review template. |
| `execution-review-checklist.md` | Standard `06-execution-review` QA readiness review checklist. |
| `release-feedback-template.md` | Standard `07-release-feedback` post-release feedback loop template. |

Rules:

- Standard-product artifacts should look here before falling back to
  qa-harness defaults.
- Requirement review handoff uses `Requirement Review Template.docx`.
- Test-case sign-off handoff under `04-test-case-review/` uses `Test Case Review Template.docx`.
- Execution readiness review under `06-execution-review/` uses
  `execution-review-checklist.md`; QA records readiness, not the final business
  release decision.
- Release feedback under `07-release-feedback/` uses
  `release-feedback-template.md`.
- Automation assessment under `05-execution/` uses
  `AutomationAssessment_Template.xlsx` only after `04-test-case-review` is
  signed off and `05-execution/01-automation-demo` has been reviewed for test
  case gaps.
- Automation assessment sign-off uses a paired
  `automation-assessment-review-<scope>.md/.docx` review form. Do not add
  `Review Time`, `Sign off Person`, execution-result, screenshot, or formal
  sign-off columns to `AutomationAssessment_Template.xlsx`.
- The `.md` template is the content source. The paired `.docx` is the approved Word layout reference generated from it.
- Generated review documents must use the v2.1 simplified sign-off layout: final sign-off near the top, reviewer name/signature captured in `Signature / Confirmation`, no duplicate `Signed Off By` row, no visible `Template` wording in the document body, and no unnecessary audit-only fields.
- Do not put `Final Decision` in the top sign-off table. Keep final approval
  decisions in the review summary, Review Trail, or final decision section so
  the sign-off block stays concise.
- Generate these human-facing review DOCX files with `D:\Workspace\qa-harness\01-system\03-tools\render_review_docx.py`, not the generic `md_docx.py` converter. `md_docx.py` is acceptable for rough AI working reviews, but it must not overwrite the formal external-share-ready review templates or final sign-off forms.
- Human review comments must be summarized into `Review Trail and Version Record`
  with affected case IDs/artifact, related version/action, and closure evidence
  before sign-off. If comments concern test cases, update
  `03-test-design/test-cases-<scope>.md`, regenerate the `.xlsx`, and update
  `03-test-design/CHANGE.md` before marking the comment fixed. If the comments
  require AI changes, keep the document `Awaiting Sign-Off` or
  `Awaiting Re-review` until the human reviewer signs again.
- Added, modified, removed, or post-sign-off scope-adjusted test cases must
  also be recorded in the workbook `Audit Trail` sheet with date, actor, change
  type, reason, affected case IDs, current scope impact, and evidence. When an
  automation assessment workbook already exists, update its `Audit Trail` too.
  Re-render the paired review DOCX after the Review Trail row is updated.
  MD-only audit notes are not acceptable.
- Use `Open Review Comments` in the conditions section as the simple gate
  signal: `None` means no open comments; any actionable comment blocks
  sign-off until the relevant artifact is updated and re-reviewed.
- For ticketing-related requirements, the Test Case Review Template's coverage
  decision must check the ticket-type split: `Admission ticket` and
  `seat-selection ticket` are separate flows unless an explicit `NA` rationale
  is recorded.
- QA2 AI working reviews do not use the human sign-off template; they stay under `03-test-design/.iterations/`.
- Keep paired `.md + .docx` for human-facing review artifacts.
- Do not use raw HTML tables or forced `<br>` line breaks in review-template markdown.
