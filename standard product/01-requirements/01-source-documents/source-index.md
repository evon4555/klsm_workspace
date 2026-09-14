# Source Document Index

## Purpose

This folder stores original source documents for the baseline product.

## Structure

- `01-it-pmo\` stores product-wide source documents.
- `02-templates\` stores product-wide templates used when generating standard-product QA artifacts.

## Template Index

| Template | Type | Required Use |
|---|---|---|
| `02-templates\TestCase_Template.xlsx` | Test case workbook template | Clone this workbook when generating `test-cases-*.xlsx`; preserve columns, styles, sample-row defaults, and blank execution fields. |
| `02-templates\TestCase_Template_pre-label.xlsx` | Legacy workbook template | Historical 19-column reference before the `Label` column; do not use unless explicitly requested. |
| `02-templates\AutomationAssessment_Template.xlsx` | Automation assessment workbook template | Clone this workbook after the automation-demo review confirms no test-case gap; keep it as the case-level automation decision matrix only. Formal sign-off belongs in `automation-assessment-review-<scope>.docx`. |
| `02-templates\Requirement Review Template.docx` | Requirement review DOCX layout | Use only for formal human-facing requirement review handoffs when a DOCX review package is requested. |
| `02-templates\Requirement Review Template.md` | Requirement review content source | Paired source for the requirement review DOCX template. |
| `02-templates\Test Case Review Template.docx` | Test case review DOCX layout | Use for final human/Test Manager test-case review sign-off packages under `04-test-case-review`. |
| `02-templates\Test Case Review Template.md` | Test case review content source | Paired source for the test-case review DOCX template. |

## Update Rule

- Keep original source documents unchanged.
- Add product-wide documents here when they apply to the baseline product.
- Add customer-specific requirement documents under the relevant customer
  project workspace.
- Project-owned templates in `02-templates\` override customer-project copies
  and qa-harness defaults for this workspace.
