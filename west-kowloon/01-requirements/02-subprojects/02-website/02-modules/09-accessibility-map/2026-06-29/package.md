# Package 2026-06-29

Module: Website Map / Accessibility Map

Package date: 2026-06-29

Package type: requirement-change

Current status: test-designed

## Source Documents

- `01-input/00-zentao requirement/requirement id.txt` - ZenTao story
  `https://lengliwh.chandao.net/story-view-4226.html`.
- `01-input/01-figma/figma.txt` - Figma UI kit node
  `node-id=20062-8236`.
- `01-input/03-prd/国际版标准官网 V1.0_总览.pdf` - PRD overview PDF.
- `01-input/03-prd/章节4.txt` - chapter 4 text extract for website map
  contents.
- `01-input/02-mindmap/` - empty as of 2026-06-29; add mindmap input here if
  it is provided later.

## Change Summary

- Defines the website map / accessibility-map content that should expose
  shortcuts for key website business areas.
- Event shortcuts use effective first-level event category names and navigate
  to the project list page with category parameters.
- Activity shortcuts use activity tags and navigate to the activity list page
  with parameters, per signed decision Q-1=a.
- Membership-card shortcuts use BU and frontend membership-card categories and
  navigate to the membership-card list page with parameters.
- Customer Service shortcuts use the Figma 4-entry set per signed decision
  Q-2=b: Register as a Member, Update Member Profile, Password Enquiry, and
  Transaction Records.
- Venue filter shortcuts use the effective venue list and navigate to the
  project list page with parameters.
- Other footer content should directly list the current footer 1 to 3 content.

## Affected Modules

- Primary: Website Map / Accessibility Map.
- Related:
  - Events / Ticketing - event category and venue-filter shortcuts navigate to
    project list pages.
  - Events - activity shortcuts navigate to activity list pages.
  - Membership Card - membership-card category shortcuts navigate to
    membership-card list pages.
  - Login and Registration - registration shortcut.
  - User Center / Orders - personal center and order query shortcuts.
  - Homepage / Footer - current footer content is reused in the map.

## Workflow Status

| Stage | Status | Location | Notes |
|---|---|---|---|
| 01-input | indexed | `01-input/input-index.md` | ZenTao story URL, Figma URL, PRD overview PDF, chapter 4 extract, and empty mindmap folder are indexed. |
| 02-analysis | signed-off | `02-analysis/requirement-consolidation-site-map.md` | Step 3.5 consolidation signed in `.docx`, absorbed back into `.md`; Q-1..Q-7 and U-1..U-6 are answered. |
| 03-test-design | complete | `03-test-design/test-cases-site-map.md` | 32 test cases authored; xlsx generated from the project template and validator passed. |
| 04-test-case-review | pending | `04-test-case-review` | No review package yet. |
| 05-execution | pending | `05-execution` | No execution evidence yet. |
| 06-execution-review | pending | `06-execution-review` | No execution readiness review recorded yet. |
| 07-release-feedback | pending | `07-release-feedback` | No release feedback recorded yet. |

## Key Outputs

- `01-input/input-index.md`
- `02-analysis/requirement-consolidation-site-map.md`
- `02-analysis/requirement-consolidation-site-map.docx`
- `03-test-design/test-cases-site-map.md`
- `03-test-design/test-cases-site-map.xlsx`
- `02-analysis/_assets/figma-site-map-node-20062-8236.png`
- `02-analysis/_assets/prd-overview-extracted-text.txt`

## Open Questions

- None. Q-1..Q-7 and U-1..U-6 are signed in
  `02-analysis/requirement-consolidation-site-map.md` and consumed by
  `03-test-design/test-cases-site-map.md`.

## Notes

- This is the first dated package under `09-accessibility-map`.
- Source-authority order for West Kowloon should be applied during analysis
  when multiple source types conflict: mindmap > PRD > Figma.
- Test-case xlsx generated from
  `D:\Workspace\west-kowloon\01-requirements\01-source-documents\02-templates\TestCase_Template.xlsx`.
