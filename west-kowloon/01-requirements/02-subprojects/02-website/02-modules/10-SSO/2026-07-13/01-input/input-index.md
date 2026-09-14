# Input Index

## Requirement Package

- Project: West Kowloon Website
- Primary module: SSO
- Related modules: Login and Registration, Website Shell / Header, Personal
  Center / Orders, CRM / Membership, WestK / myWestK / M+ / HKPM SP sites,
  Security / Platform
- Package: `2026-07-13`
- Canonical location:
  `D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\10-SSO\2026-07-13`

This package covers the unified C-end SSO requirement where AnTank becomes the
single login/registration/forgot-password entry and OAuth IdP for WestK-family
SP sites.

## Source Files

### ZenTao

- `00-zentao requirement\requirement id.txt` - story URL
  `https://lengliwh.chandao.net/story-view-4305.html`.
- Status: URL captured only. Authenticated ZenTao content has not been pulled
  into this package.

### Figma

- `01-figma\` - folder exists but is empty as of 2026-07-13.
- Status: no Figma URL, screenshot, or MCP design context is available in this
  package.

### Mindmap

- `02-mindmap\` - folder exists but is empty as of 2026-07-13.
- Per West Kowloon source-authority rule, if a narrow mindmap branch is added
  later, analysis must be revised in place.

### PRD

- `03-prd\AnTank-consumer-unified-SSO-业务专版.20260617.pdf` - business /
  product-manager version, v1.0/v1.1 draft dated 2026-06-17.
  - Direct requirement areas: background and goal, AnTank as unified login
    entry, user categories, SP site changes, new registration, optional global
    logout, data sync, security, implementation checklist, pending decisions.
- `03-prd\AnTank-consumer-unified-SSO-design.20260617.zh-CN.pdf` - technical
  design version, v1.0 draft dated 2026-06-17.
  - Direct requirement areas: AnTank as IdP, WestK-family sites as SPs, OAuth
    2.0 authorization-code flow, Checking API, `/services/oauth2/authorize`,
    `/services/oauth2/token`, `/s/register`, `/s/user-session-sync`,
    `/SingleSignOut`, optional SSO broadcast, old WestK Email user three-step
    authentication, migration table, token payload, security rules, and pending
    questions.

### Extracted Analysis Assets

- `..\02-analysis\_assets\AnTank-consumer-unified-SSO-业务专版.20260617.extracted.txt`
  - Extracted with PyMuPDF on 2026-07-13; 13 pages.
- `..\02-analysis\_assets\AnTank-consumer-unified-SSO-design.20260617.zh-CN.extracted.txt`
  - Extracted with PyMuPDF on 2026-07-13; 27 pages.

## Source Authority Notes

- Project rule: mindmap > PRD > Figma.
- This package currently has no mindmap and no Figma input, so the two PRD PDFs
  are the working source for scope.
- The design PDF provides the more detailed technical implementation model; the
  business PDF provides product-facing intent and pending business decisions.
- PRD-only items are in scope under the West Kowloon PRD-fills-gap rule, but
  items explicitly marked "待确认" remain pending until sign-off.

## Analysis Outputs

- `..\02-analysis\rag-retrieval.md` - current-repo / local mock retrieval
  notes before test design.
- `..\02-analysis\requirement-consolidation-sso.md` - Step 3.5 requirement
  consolidation and sign-off gate.
- `..\02-analysis\requirement-consolidation-sso.docx` - generated human review
  copy after the markdown draft is produced.
