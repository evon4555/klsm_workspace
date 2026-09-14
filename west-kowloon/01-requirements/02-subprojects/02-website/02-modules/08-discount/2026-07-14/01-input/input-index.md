# Input Index

## Requirement Package

- Project: West Kowloon Website
- Primary module: Discount and Member Benefits
- Related modules: Ticketing, Payment, Login and Registration, Membership Card
- Package: `2026-07-14`
- Scope slug: `priority-booking-c-end-optimization`
- Canonical location:
  `D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\08-discount\2026-07-14`

This package covers the Website C-end priority-booking optimization for project
detail pages. It treats the 2026-07-14 requirement change like a new
requirement evaluation, while using the 2026-06-25 bank-card priority-purchase
test cases and screenshots as reference inputs.

## Source Files

### PRD

- `03-prd\国际版标准官网 V1.2.2-银行卡优先购C端优化.zip` - original PRD package received for 2026-07-14.
- `03-prd\extracted\国际版标准官网 V1.2.2-银行卡优先购C端优化.md` - extracted PRD markdown for analysis.
- `03-prd\extracted\图片和附件\优先购C端流程交互原型V1.html` - comprehensive C-end priority-booking interaction prototype.
- `03-prd\extracted\图片和附件\bank-card-presale-visa-only-demo-v1.html` - single bank-card priority-purchase prototype.
- `03-prd\extracted\图片和附件\image.png` - PRD image asset.
- `03-prd\extracted\图片和附件\c3af75b55f8a52a56842b79a875cea8f.png` - PRD image asset.

### Figma

- `01-figma\figma.txt` - UI-kit Figma URL:
  `https://www.figma.com/design/QO8xVUE4jWzBS0Z1eKpcrb/...node-id=22993-226241`.

### Mindmap

- `02-mindmap\` - empty as of 2026-07-15. No narrow mindmap capture has been provided for this package.

### Prior-Version Reference

- Prior package: `..\2026-06-25`.
- Prior consolidation:
  `..\2026-06-25\02-analysis\requirement-consolidation-bank-card-priority-purchase.md`.
- Prior test cases:
  `..\2026-06-25\03-test-design\test-cases-bank-card-priority-purchase.xlsx`.
- Prior embedded screenshots / image references: the prior workbook contains embedded images and should be used as a visual reference when designing the new C-end cases.

## Scope Notes

- Source-authority order remains mindmap > PRD > Figma. Because no mindmap is available, the extracted PRD markdown is the current working authority and Figma is UI reference.
- This is not a mechanical patch of the 2026-06-25 test cases. The changed business flow starts from the project detail page and priority-booking policy area.
- Future test case generation must reference the previous version's test cases and screenshots for continuity, then design cases according to the 2026-07-14 business flow.
- Changed cells or rows in future regenerated workbooks must use yellow highlight per the project change-management rule.
