# Input Index

## Requirement Package

- Project: West Kowloon Website
- Primary module: Website Map / Accessibility Map
- Related modules: Ticketing / Events, Activities, Membership Card, Login and
  Registration, Personal Center / Orders, Footer
- Package: `2026-06-29`
- Canonical location:
  `D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\09-accessibility-map\2026-06-29`

This package covers the website map / site map page under the website
accessibility workstream. The page exposes quick links for business areas,
member service entries, venue filters, and selected existing footer content.

## Source Files

### ZenTao

- `00-zentao requirement\requirement id.txt` - story URL
  `https://lengliwh.chandao.net/story-view-4226.html`.
- Status: URL captured only. Authenticated ZenTao content has not been pulled
  into this package.

### Figma

- `01-figma\figma.txt` - Figma UI kit node
  `QO8xVUE4jWzBS0Z1eKpcrb`, node `20062:8236`.
- `..\02-analysis\_assets\figma-site-map-node-20062-8236.png` - local
  screenshot captured from Figma MCP on 2026-06-29 for analysis reference.
- Figma confirms the page is named `网站地图` / `Site Map` and shows sections
  such as Buy Tickets, Activities, Membership, Customer Service, Venues, The
  Authority, The District, and News & Support.

### Mindmap

- `02-mindmap\` - folder exists but is empty as of 2026-06-29.
- Per West Kowloon source-authority rule, if a narrow mindmap branch is added
  later, analysis must be revised in place.

### PRD

- `03-prd\鍥介檯鐗堟爣鍑嗗畼缃?V1.0_鎬昏.pdf` - PRD overview PDF. Relevant extracted
  areas:
  - page 6: accessibility mode is non-standard, references WCAG 2.1, and lists
    website map as new V1.2 scope.
  - page 7: footer ad positions `foot_1` to `foot_7`; website map source later
    refers to existing footer 1 to 3 content.
  - page 8: section 4.1 网站地图, the direct requirement text for this package.
- `03-prd\章节4.txt` - chapter 4 text extract for section 4.1 网站地图.

## Source Authority Notes

- Project rule: mindmap > PRD > Figma.
- This package currently has no mindmap source, so the PRD section 4.1 extract
  is the working source for scope.
- Figma is a reference for page grouping, labels, and example entries. It does
  not override PRD rules when the two disagree.
- PRD-only items are in scope under the West Kowloon PRD-fills-gap rule.

## Analysis Outputs

- `..\02-analysis\requirement-consolidation-site-map.md` - Step 3.5
  requirement consolidation and sign-off gate.
- `..\02-analysis\requirement-consolidation-site-map.docx` - generated human
  review copy after the markdown draft is produced.

