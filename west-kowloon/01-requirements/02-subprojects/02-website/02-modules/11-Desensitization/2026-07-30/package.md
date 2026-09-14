# Package 2026-07-30

Module: Desensitization

Package date: 2026-07-30

Package type: new-requirement

Current status: Test-case review signed off; ready for execution

## Source Documents

- `01-input/00-zentao requirement/requirement id.txt` - ZenTao story `4319` and cross-module scope summary.
- `01-input/00-zentao requirement/checking rules.txt` - masking examples for phone, email, name, ID, address, birthday and gender.
- `01-input/01-figma/` - empty as of 2026-07-30.
- `01-input/02-mindmap/` - empty as of 2026-07-30.
- `01-input/03-prd/` - empty as of 2026-07-30.

## Change Summary

- Introduces a cross-module PII desensitization requirement covering Website,
  PDA, backend and BI surfaces.
- Signed scope includes all seven PII categories: phone, email, name, ID,
  address, birthday and gender.
- Generates one Chinese cross-module Test Cases Sheet with module-specific
  Module/Feature values and descriptions.
- Signed exclusions are BI Dashboard, permissions/audit, KMS/centralized
  storage, complex format boundaries, multilingual checks and old-case updates.

## Affected Modules

- Primary: Desensitization / shared PII protection.
- Related:
  - Website Login / Personal Center.
  - Membership Card and activation information.
  - Admission ticket and seat-selection ticket order detail, ticket wallet and
    admission code.
  - PDA scan result.
  - Backend Member 360, ticket orders, membership-card orders/list/detail and
    reports.
  - BI custom reports, excluding Dashboard.

## Workflow Status

| Stage | Status | Location | Notes |
|---|---|---|---|
| 01-input | indexed | `01-input/input-index.md` | ZenTao summary and rule examples indexed; Figma, mindmap and PRD folders are empty. |
| 02-analysis | signed off | `02-analysis/requirement-consolidation-desensitization.md` | Wang Yifan answered Q-1..Q-13 and U-1..U-6 on 2026-07-30. |
| 03-test-design | signed off | `03-test-design/test-cases-desensitization.xlsx` | v1.3 contains 47 Chinese cases; Test Manager signed off after removing `SIT-TC-WK-PII-048`. |
| 04-test-case-review | signed off | `04-test-case-review/test-case-review-desensitization.md` | Formal DOCX signed by Wang Yifan on 2026-08-12; no open review comments. |
| 05-execution | ready | `05-execution` | Ready to start execution. |
| 06-execution-review | pending | `06-execution-review` | Not started. |
| 07-release-feedback | pending | `07-release-feedback` | Not started. |

## Key Outputs

- `01-input/input-index.md`
- `02-analysis/rag-retrieval.md`
- `02-analysis/requirement-consolidation-desensitization.md`
- `02-analysis/requirement-consolidation-desensitization.docx`
- `03-test-design/test-cases-desensitization.md`
- `03-test-design/test-cases-desensitization.xlsx`
- `03-test-design/CHANGE.md`
- `03-test-design/.iterations/test-case-review-desensitization-r1.md`
- `04-test-case-review/test-case-review-desensitization.md`
- `04-test-case-review/test-case-review-desensitization.docx`

## Open Questions

- None for the signed test-design scope.

## Notes

- The final test cases are Chinese.
- The cross-module scope will be represented through explicit Module/Feature
  values, not one generic desensitization scenario.
- Existing AUTH, ticketing and SSO cases were used only as retrieval references;
  no older workbook was modified.
