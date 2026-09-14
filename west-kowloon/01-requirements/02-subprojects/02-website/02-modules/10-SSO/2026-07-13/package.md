# Package 2026-07-13

Module: SSO

Package date: 2026-07-13

Package type: new-requirement

Current status: test-case review signed off; execution in progress

## Source Documents

- `01-input/00-zentao requirement/requirement id.txt` - ZenTao story
  `https://lengliwh.chandao.net/story-view-4305.html`.
- `01-input/03-prd/AnTank-consumer-unified-SSO-业务专版.20260617.pdf` -
  product/project-manager version of the unified C-end SSO requirement.
- `01-input/03-prd/AnTank-consumer-unified-SSO-design.20260617.zh-CN.pdf` -
  development design version of the unified SSO architecture.
- `01-input/01-figma/` - folder exists but is empty as of 2026-07-13.
- `01-input/02-mindmap/` - folder exists but is empty as of 2026-07-13.

## Change Summary

- Cancels the old WestK Customer Portal C-end login page as a customer-facing
  entry and makes AnTank the unified login, registration, and forgot-password
  entry.
- Defines WestK, myWestK, M+, HKPM, and the AnTank ticketing website as SP
  sites that integrate with AnTank as OAuth IdP.
- Adds Checking API, authorization endpoint, token endpoint, register endpoint,
  session sync endpoint, optional SSO login broadcast, and optional global SSO
  logout.
- Adds compatibility for existing WestK Email users through a migration table
  plus server-side three-step WestK Customer Portal authentication.
- Adds cross-system account linking and data-preparation needs for
  `westk_legacy_accounts`, `openmember`, `member.westk_sync`, SP client
  configuration, redirect URI whitelist, source Channel Name, and checkAuth URL.

## Affected Modules

- Primary: SSO.
- Related:
  - Login and Registration - existing native login, OTP login, third-party
    login, forgot password, and registration flows are reused inside the SSO
    entry.
  - Website shell / header - login/register/logout links redirect to AnTank or
    invoke the SSO flow.
  - WestK / myWestK / M+ / HKPM SP websites - must consume OAuth codes/tokens
    and establish local sessions.
  - Personal Center / Orders - authenticated state and order visibility depend
    on SSO identity.
  - CRM / membership - old user migration data and optional registration sync.
  - Security / platform - client credentials, JWT, signing, nonce, PII
    encryption, audit logs, retry, and DLQ.

## Workflow Status

| Stage | Status | Location | Notes |
|---|---|---|---|
| 01-input | indexed | `01-input/input-index.md` | ZenTao story URL and two PRD PDFs indexed; Figma and mindmap folders are empty. |
| 02-analysis | signed off | `02-analysis/requirement-consolidation-sso.md` | Q-1..Q-15 reviewer answers captured; human sign-off date/signature validated; Open Review Comments synchronized to None. |
| 03-test-design | QA2 reviewed | `03-test-design/test-cases-sso.md` | 24 SIT SSO cases generated under the signed first-round scope; paired workbook generated from the official template; QA2 review passed. |
| 04-test-case-review | signed off | `04-test-case-review/test-case-review-sso.md` | Test Manager sign-off received on 2026/07/13 with Signature / Confirmation `Wang Yifan Evan`; no open review comments. |
| 05-execution | in progress | `05-execution` | Execution evidence capture has started. |
| 06-execution-review | pending | `06-execution-review` | No execution readiness review recorded yet. |
| 07-release-feedback | pending | `07-release-feedback` | No release feedback recorded yet. |

## Key Outputs

- `01-input/input-index.md`
- `02-analysis/_assets/AnTank-consumer-unified-SSO-业务专版.20260617.extracted.txt`
- `02-analysis/_assets/AnTank-consumer-unified-SSO-design.20260617.zh-CN.extracted.txt`
- `02-analysis/rag-retrieval.md`
- `02-analysis/requirement-consolidation-sso.md`
- `02-analysis/requirement-consolidation-sso.docx`
- `03-test-design/test-cases-sso.md`
- `03-test-design/test-cases-sso.xlsx`
- `03-test-design/CHANGE.md`
- `03-test-design/.iterations/test-case-review-sso-r1.md`
- `04-test-case-review/test-case-review-sso.md`
- `04-test-case-review/test-case-review-sso.docx`

## Signed Scope Notes

- See `02-analysis/requirement-consolidation-sso.md` sections 7A and 8.
- Q-1..Q-15 reviewer answers narrow first-round execution to the local mock SP
  `http://127.0.0.1:6080/login`; real external SPs, WestK API contract testing,
  CRM sync details, AuthCode expiry, QPS/performance scope, and App WebView are
  excluded or ignored for this package unless a later signed update reopens
  them.
- Requirement consolidation is signed off. Initial test design is generated,
  QA2 review passed, and Test Manager test-case sign-off was received on
  2026/07/13. Execution evidence capture can proceed.

## Notes

- The source PDFs are drafts and contain several "待确认" items. Treat those
  as sign-off questions, not as settled implementation facts.
- Existing login-registration SSO cases
  `SIT-TC-WEB-AUTH-014` and `SIT-TC-WEB-AUTH-039..041` are current-repo
  references only. This package should create its own SSO integration case set
  after sign-off.
