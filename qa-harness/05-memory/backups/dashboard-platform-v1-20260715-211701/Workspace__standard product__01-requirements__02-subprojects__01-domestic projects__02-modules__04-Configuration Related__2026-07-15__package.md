# Package 2026-07-15

Module: Configuration Related

Package date: 2026-07-15

Package type: standard-product requirement evaluation

Current status: test-case review signed off; ready for execution

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
| 03-test-design | reviewed | `03-test-design/test-cases-batch-session-configuration.md`; `03-test-design/test-cases-batch-session-configuration.xlsx` | 15 draft cases generated from signed scope, translated to English-only wording, exported to the standard-product workbook template, and QA2 self-checked. |
| 04-test-case-review | signed-off | `04-test-case-review/test-case-review-batch-session-configuration.md`; `04-test-case-review/test-case-review-batch-session-configuration.docx` | Test Manager signed off the English-only v1.1 review package on 2026-07-15. |
| 05-execution | ready | `05-execution` | Ready to start execution. |
| 06-release | pending | `06-release` | Not started. |

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

## Gate

Requirement scope and test-case review are signed off. Test design has been
drafted, translated to English-only wording, exported to the standard-product
workbook template, QA2 self-checked, and approved by Test Manager. Execution is
ready to start.
