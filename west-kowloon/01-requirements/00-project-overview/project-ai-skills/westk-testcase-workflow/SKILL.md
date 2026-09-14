---
name: westk-testcase-workflow
description: Project-owned workflow for West Kowloon test case design, test case generation, QA2 review, test case revision, workbook regeneration, project test case templates, ticket-type split coverage, Admission ticket, seat-selection ticket, and selecting the correct QA harness skill/template before producing or reviewing cases.
---

# WestK Test Case Workflow

## Source Of Truth

This file is the portable project-owned skill. User-local agent skills should
delegate to this file instead of duplicating the workflow.

## Required Indexes

Before writing or reviewing West Kowloon test cases, read:

- `D:\Workspace\qa-harness\01-system\01-skills\README.md`
- `D:\Workspace\qa-harness\01-system\02-qa-workflow.md`
- `D:\Workspace\west-kowloon\01-requirements\00-project-overview\project-context.md`
- `D:\Workspace\west-kowloon\01-requirements\01-source-documents\source-index.md`
- `D:\Workspace\west-kowloon\01-requirements\01-source-documents\02-templates\README.md`

## Skill Routing

Read the matching harness skill before acting:

- New test case design:
  `D:\Workspace\qa-harness\01-system\01-skills\write-test-case\SKILL.md`
- QA2 review:
  `D:\Workspace\qa-harness\01-system\01-skills\review-test-case\SKILL.md`
- Iterative AI write/review/revise loop:
  `D:\Workspace\qa-harness\01-system\01-skills\iterate-test-case-quality\SKILL.md`
- Revision after review:
  `D:\Workspace\qa-harness\01-system\01-skills\revise-test-case\SKILL.md`
- Requirement-change maintenance:
  `D:\Workspace\qa-harness\01-system\01-skills\maintain-requirement-change\SKILL.md`
- Human review/sign-off lifecycle:
  `D:\Workspace\qa-harness\01-system\01-skills\manage-review-signoff\SKILL.md`

If translation is involved, also read:

`D:\Workspace\west-kowloon\01-requirements\00-project-overview\project-ai-skills\westk-zh-en-translation\SKILL.md`

If Test Manager sign-off, review comments, or `04-test-case-review` is involved,
also read:

`D:\Workspace\west-kowloon\01-requirements\00-project-overview\project-ai-skills\westk-review-signoff\SKILL.md`

## West Kowloon Case Generation Rules

- Use the project workbook template:
  `D:\Workspace\west-kowloon\01-requirements\01-source-documents\02-templates\TestCase_Template.xlsx`
- Preserve the template columns, order, styling, and design-time blank fields.
- Regenerate `.xlsx` by cloning the template, not by creating a fresh workbook.
- For ticketing/cart/checkout/payment/discount/refund/wallet/order-detail
  scopes, treat `Admission ticket` and `seat-selection ticket` as separate
  flows unless one flow has an explicit `NA` rationale.

## Review Rules

- QA2 reviews stay under `03-test-design/.iterations/`.
- Human/Test Manager sign-off belongs under `04-test-case-review/`.
- Missing `Admission ticket` or `seat-selection ticket` coverage is a gap for
  West Kowloon ticketing-related scopes unless documented as `NA`.
- If review comments require case changes, update the test cases, regenerate
  the workbook, update `CHANGE.md`, update workbook `Audit Trail` sheet(s),
  regenerate the review DOCX, and keep human sign-off awaiting re-review.
- Added, modified, removed, or post-sign-off scope-adjusted cases must be
  visible in both the `.xlsx` `Audit Trail` sheet and the `04-test-case-review`
  DOCX `Review Trail and Version Record`. Use
  `D:\Workspace\qa-harness\01-system\03-tools\record_testcase_change.py` where
  possible; MD-only audit notes are not acceptable.

## Formal Requirement Review Gate

For West Kowloon Step 3.5 requirement consolidation, the human-facing
`requirement-consolidation-<scope>.md/.docx` pair must use the formal
Requirement Review Template v2.1 structure, not an ad hoc consolidation-only
layout.

The `.md` must include these template sections:

- `Final Sign-off`
- `Review Summary`
- `Reviewed Sources`
- `Review Trail and Version Record`
- `Scope Decision`
- `Requirement Quality Decision`
- `Review Findings`
- `Conditions and Next Step`

Place the consolidation analysis details inside the formal document, for
example as `Requirement Analysis Detail`. Render the `.docx` with
`D:\Workspace\qa-harness\01-system\03-tools\render_review_docx.py`. Do not
use generic `md_docx.py` for formal West Kowloon requirement sign-off forms.

## Validation

Run relevant checks after changes:

- `python D:\Workspace\qa-harness\01-system\03-tools\check_workflow_coverage.py`
- `python D:\Workspace\qa-harness\01-system\03-tools\validate_testcase_xlsx.py <xlsx>`
- `python D:\Workspace\qa-harness\01-system\03-tools\check_testcase_review_gate.py --xlsx <xlsx> --strict`
- `python D:\Workspace\qa-harness\01-system\03-tools\check_rule_drift.py --requirements-dir D:\Workspace`
