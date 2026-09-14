# Package <yyyy-mm-dd[-story-id-topic]>

Module: <module name>

Package date: <yyyy-mm-dd>

Package type: <baseline | requirement-change | migration | hotfix>

Current status: <draft | analysis | requirement-signed | test-designed | qa2-reviewed | test-case-review-signed | executed | execution-reviewed | release-feedback | active-reference>

## Source Documents

- <path to source PRD, Figma, mindmap, ticket, or migrated package>

## Change Summary

- <what changed>
- <why this package exists>

## Affected Modules

- Primary: <module>
- Related: <other modules, or none>

## Workflow Status

| Stage | Status | Location | Notes |
|---|---|---|---|
| 01-input | <status> | `01-input` | <notes> |
| 02-analysis | <status> | `02-analysis` | `requirement-consolidation-<scope>.md` + `.docx`; `.docx` uses `Requirement Review Template.docx`; blocks `03-test-design` until Signed Off |
| 03-test-design | <status> | `03-test-design` | latest `test-cases-<scope>.md/.xlsx`; QA2 review artifacts under `.iterations/` |
| 04-test-case-review | <status> | `04-test-case-review` | Test Manager sign-off form only; `.docx` uses `Test Case Review Template.docx`; `Open Review Comments` must be `None` before signed-off/ready |
| 05-execution | <status> | `05-execution` | <notes> |
| 06-execution-review | <status> | `06-execution-review` | QA readiness outcome: Ready for Release / Ready for Release with Accepted Risk / Not Ready - Fix Required / Blocked / Scope Change Required |
| 07-release-feedback | <status> | `07-release-feedback` | post-release feedback, production issues, hotfix/rollback notes, accepted-risk follow-up, and future improvement items |

## Key Outputs

- <path to important workbook, review, evidence, or release file>

## Open Questions

- <question, owner, and next action>

## Notes

- <migration, archive, or operational notes>
