---
name: manage-review-signoff
description: Use this skill after QA2 test-case review or requirement review when a human-facing review/sign-off document must be prepared, updated from reviewer comments, re-rendered to DOCX, or synced after Test Manager/Product Owner sign-off.
---

# Manage Review Sign-off

## Purpose

Manage the human review/sign-off lifecycle for requirement review and
test-case review artifacts. This skill is not the QA2 review itself; it governs
the handoff, reviewer comments, version closure, and signed-off status.

## Inputs

- Requirement review or test-case review `.md` and paired `.docx`.
- Reviewer-edited DOCX, when comments or sign-off were entered in Word.
- Affected requirement consolidation or test-case files.
- For test-case comments: `03-test-design/test-cases-<scope>.md`, the paired
  `.xlsx`, and `03-test-design/CHANGE.md`.

## Workflow

1. Read the reviewer-edited DOCX tables and check for Word comment parts.
2. If actionable comments exist, keep the review awaiting re-review/sign-off.
3. Update the affected canonical artifact first.
4. Regenerate derived artifacts such as `.xlsx`.
5. Update `CHANGE.md` when test cases changed.
6. Record comments, affected artifacts, version/action, closure evidence, and
   status in `Review Trail and Version Record`.
7. For any test-case add, modify, remove, or post-sign-off scope adjustment,
   also update the workbook `Audit Trail` sheet in the affected
   `test-cases-<scope>.xlsx` and, when it already exists, the paired
   `automation-assessment-<scope>.xlsx`. Use
   `01-system/03-tools/record_testcase_change.py` for this writeback. MD-only
   audit notes are not acceptable.
8. Render the formal DOCX with `01-system/03-tools/render_review_docx.py` when
   the project requires the professional review layout.
9. Only after the human reviewer removes comments and fills sign-off date plus
   signature, sync status to `Signed Off` and update package/module indexes.

## Sign-off Gate

The human reviewer only needs to fill `Sign-off Date` and
`Signature / Confirmation`. AI / QA automation owns synchronization of
system-maintained fields such as `Final Status`, `Open Review Comments`,
`Final Comments`, `Handoff Decision`, review-trail closure status, and
package/module workflow status after the human inputs are validated.

Do not ask the reviewer to fill `Open Review Comments` or workflow status
fields manually. For long review DOCX files, highlight only the human input
fields that need the reviewer action.

Do not mark a review signed off when `Open Review Comments` contains actionable
comments. `None`, blank, or `-` means no open comments. A signed review must
have:

- `Final Status` = `Signed Off`
- `Sign-off Date`
- `Signature / Confirmation`
- no Word comments in the paired DOCX
- no current open blocker in the last review-trail status
- project-specific coverage gates satisfied or explicitly marked `NA`, such as
  West Kowloon `Admission ticket` versus `seat-selection ticket` split for
  ticketing-related scopes

## Output

- Updated review `.md`
- Re-rendered formal `.docx`
- Updated affected requirement/test-case artifact
- Updated `.xlsx`, workbook `Audit Trail`, and `CHANGE.md` when test cases changed
- Updated package/module status when sign-off state changes
