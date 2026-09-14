---
name: westk-review-signoff
description: Project-owned workflow for West Kowloon requirement review and test-case review sign-off, including 04-test-case-review, Test Manager sign-off, reviewer comments in DOCX, Review Trail and Version Record updates, formal review DOCX rendering, signed-off status sync, and execution-readiness checks.
---

# WestK Review Sign-off

## Source Of Truth

This file is the portable project-owned skill. User-local agent skills should
delegate to this file instead of becoming the only copy of the workflow.

## Core Rule

Treat markdown as the canonical content source and DOCX as the human
review/sign-off surface. For formal human-facing review DOCX, use:

`D:\Workspace\qa-harness\01-system\03-tools\render_review_docx.py`

Do not use generic `md_docx.py` for final external-share-ready sign-off forms.

## Required Templates

- Requirement review:
  `D:\Workspace\west-kowloon\01-requirements\01-source-documents\02-templates\Requirement Review Template.docx`
- Test case review:
  `D:\Workspace\west-kowloon\01-requirements\01-source-documents\02-templates\Test Case Review Template.docx`

## Test-Case Review Workflow

When handling `04-test-case-review/test-case-review-<scope>.docx`:

1. Read DOCX tables and check for Word comments such as `word/comments.xml`.
2. If actionable human review comments exist, the document cannot remain signed
   off.
3. Update `03-test-design/test-cases-<scope>.md` first.
4. Regenerate the `.xlsx` from the approved workbook template.
5. Update `03-test-design/CHANGE.md`.
6. Update `Review Trail and Version Record` with reviewer, comment summary,
   affected artifacts, version/action, closure evidence, and status.
7. For any added, modified, removed, or post-sign-off scope-adjusted test case,
   update the workbook `Audit Trail` sheet in
   `03-test-design/test-cases-<scope>.xlsx` and, when present,
   `05-execution/02-automation-assessment/automation-assessment-<scope>.xlsx`.
   Use `D:\Workspace\qa-harness\01-system\03-tools\record_testcase_change.py`
   where possible so the xlsx audit row, review trail row, and regenerated
   DOCX stay aligned. MD-only audit notes are not acceptable.
8. Keep `Final Status` as `Awaiting Re-review` or `Awaiting Sign-Off` until the
   human reviewer signs again.
9. Regenerate the formal DOCX with `render_review_docx.py`.

AI must not self-sign after changing reviewed artifacts.

## Human Sign-off Sync

Human reviewers only need to fill the human input fields:

- `Sign-off Date`
- `Signature / Confirmation`

AI / QA automation owns the system-maintained fields after validating the human
inputs and comment state:

- `Final Status`
- `Open Review Comments`
- `Final Comments`
- `Handoff Decision`
- review-trail closure status
- package and module index workflow status

Do not ask the reviewer to fill `Open Review Comments` or workflow status
fields. These fields must be synchronized by AI / QA automation before moving
to the next phase.

Only sync a review document to `Signed Off` when all are true:

- `Sign-off Date` is filled.
- `Signature / Confirmation` is filled.
- `Open Review Comments` is `None`, blank, or `-`.
- No actionable comments remain in DOCX table content.
- No Word comments part remains in the DOCX.

After valid sign-off:

- Update canonical `.md` status to `Signed Off`.
- Add a final review-trail row with no-open-comments and human sign-off
  evidence.
- Set execution readiness to ready only when no blockers remain.
- Regenerate formal `.docx`.
- Update package and module indexes.

## Formatting Rules

- Do not show `Template` in generated document body.
- Do not include a separate `Signed Off By` row.
- Do not add a separate `Final Decision` section or row.
- Put reviewer name/signature only in `Signature / Confirmation`.
- When a DOCX is awaiting human sign-off, highlight only the fields the
  reviewer must fill: `Sign-off Date` and `Signature / Confirmation`. Do not
  require the reviewer to find or edit system-maintained status fields in the
  body of a long review document.
- Use the bottom `Conditions and Next Step` table with
  `Open Review Comments`, `Next Folder / Phase`, and `Handoff Decision`.
- Historical `Needs Revision` rows are history, not current blockers, if a
  later row fixes or closes them.

## Quality Gate Expectation

The package is not execution-ready unless matching test-case review is signed,
dated, and free of open comments. For ticketing-related scopes, review evidence
should also show `Admission ticket` and `seat-selection ticket` were considered
separately or explicitly marked `NA`.
