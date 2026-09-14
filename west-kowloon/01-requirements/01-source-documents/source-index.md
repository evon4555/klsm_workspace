# Source Document Index

## Purpose

This folder stores original project-level source documents for the West Kowloon
project.

These files are not a single Website requirement package. They are project-wide
references that can be used when analyzing concrete requirements under each
workstream.

## IT-PMO Documents

Location:

- `01-it-pmo\IT-PMO-410-Requirement-Document_V1.0.pdf`
- `01-it-pmo\IT-PMO-420-Functional-Specification-Document_V1.0_0414.docx`

Usage:

- Treat these as project-level requirement and functional specification sources.
- Use them to understand overall scope, business rules, system areas,
  integrations, and cross-channel impact.
- When a concrete requirement package conflicts with these documents, the
  concrete requirement package should be treated as the latest working input
  unless the project team confirms otherwise.

## Templates

Location:

- `02-templates\TestCase_Template.xlsx`
- `02-templates\Requirement Review Template.md`
- `02-templates\Requirement Review Template.docx`
- `02-templates\Test Case Review Template.md`
- `02-templates\Test Case Review Template.docx`

Usage:

- Use `D:\Workspace\qa-harness\01-system\01-skills\write-test-case\SKILL.md`
  before generating West Kowloon test cases.
- Use `02-templates\TestCase_Template.xlsx` as the authoritative test case
  workbook schema. Generated workbooks must clone this template and swap data
  in; do not rebuild a workbook from scratch.
- Use `D:\Workspace\qa-harness\01-system\01-skills\review-test-case\SKILL.md`
  before QA2 review of generated test cases.
- Use the requirement review template for human-facing requirement / scope
  sign-off documents.
- Use the test case review template for Test Manager final sign-off documents
  under `04-test-case-review`.
- The review template `.md` files are the content source. The paired `.docx`
  files are the approved Word layout reference generated from those sources.
- Formal review DOCX files must be rendered with
  `D:\Workspace\qa-harness\01-system\03-tools\render_review_docx.py`.
- Human-facing review forms use `Open Review Comments` as the gate signal:
  `None` allows sign-off; actionable comments require artifact updates,
  version records, and human re-review before sign-off.
- Ticketing-related test case generation and review must consider
  `Admission ticket` and `seat-selection ticket` separately, or document the
  explicit `NA` rationale.
- Chinese-to-English translation of West Kowloon materials should use the
  project-owned skill
  `D:\Workspace\west-kowloon\01-requirements\00-project-overview\project-ai-skills\westk-zh-en-translation\SKILL.md` and follow the approved style anchor
  `D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\08-discount\2026-07-07\03-test-design\test-cases-promo-code-bank-card-offer.xlsx`.

## Update Rule

- Keep original source documents unchanged.
- Add new project-wide documents here when they apply to multiple workstreams or
  multiple requirements.
- Add requirement-specific documents under the relevant requirement package
  instead.
