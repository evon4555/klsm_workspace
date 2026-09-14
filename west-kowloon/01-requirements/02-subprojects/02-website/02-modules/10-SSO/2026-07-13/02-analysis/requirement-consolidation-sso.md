# Requirement Review and Approval

Format version: 2.1

| Item | Value |
|----|----|
| Organization | West Kowloon Cultural District Authority / Antank |
| Project / Program | TP2 - WestK New Ticketing Website |
| Requirement Package | `10-SSO/2026-07-13` |
| Requirement Scope | Unified C-end SSO - AnTank as single login entry and OAuth IdP |
| Review Target | `02-analysis/requirement-consolidation-sso.md` |
| Review Type | Requirement baseline / change review |
| Prepared By | QA1 |
| Review Date | 2026-07-13 |
| Final Status | Signed Off |

## 1. Final Sign-off

Put the final reviewer name in the `Signature / Confirmation` row.

| Sign-off Field | Value |
|----|----|
| Role | Test Manager / Product Owner / Business Owner |
| Sign-off Date | 2026/07/13 |
| Signature / Confirmation | Wang Yifan Evan |
| Final Comments | Signed off for first-round SSO test design with Q-1..Q-15 answers captured. System-maintained status fields have been synchronized by QA after validating the human sign-off date and signature. |

## 2. Review Summary

| Summary Item | Result |
|----|----|
| Scope Readiness | Ready for test design - requirement consolidation signed off |
| Key Business Risk | High - cross-site authentication, legacy WestK account migration, OAuth token exchange, and optional broadcast/logout behavior can block login or create incorrect identity state across WestK-family sites. |
| Open Decisions | Closed for first-round SSO test design. Q-1..Q-15 answers are signed off; U-1..U-8 remain accepted working assumptions unless a later signed update reopens them. |
| Regression Impact | High |
| Summary | This package introduces AnTank as the single customer-facing C-end login, registration, and forgot-password entry, and as the OAuth IdP for SP integration. Reviewer answers scope the first executable round to the local mock SP `http://127.0.0.1:6080/login`; external SP sites can be omitted. Existing login-registration SSO smoke cases are references only; a dedicated SSO integration test set must be generated after formal Test Manager sign-off. |

## 3. Reviewed Sources

| Source / Artifact | Authority | Location | Version / Date | Status |
|----|----|----|----|----|
| SSO business requirement PDF | Primary working source | `01-input/03-prd/AnTank-consumer-unified-SSO-业务专版.20260617.pdf` | v1.0 / v1.1 draft, 2026-06-17 | Reviewed |
| SSO technical design PDF | Primary working source | `01-input/03-prd/AnTank-consumer-unified-SSO-design.20260617.zh-CN.pdf` | v1.0 draft, 2026-06-17 | Reviewed |
| Extracted PDF text | Derived evidence | `02-analysis/_assets/*.extracted.txt` | Extracted 2026-07-13 | Reviewed |
| Mindmap / Process Flow | Primary if later provided | `01-input/02-mindmap/` | Empty as of 2026-07-13 | NA |
| Figma / UI Design | Reference | `01-input/01-figma/` | Empty as of 2026-07-13 | NA |
| Prior signed-off package | Reference | `../01-login-registration/2026-06-16` | Existing login-registration package | Reviewed as impact reference |
| Change request / story | Reference | `https://lengliwh.chandao.net/story-view-4305.html` in `01-input/00-zentao requirement/requirement id.txt` | Story 4305 | URL captured only; authenticated story body not exported |
| Local SSO SP mock | Execution helper reference | `C:\Users\klsm\Downloads\westk-consumer-sso-sp-mock` | Local Vue mock | Reviewed as optional execution helper only |

## 4. Review Trail and Version Record

Record each review round, summarize review comments, update the affected requirement artifact first, and link the closure evidence before the next sign-off. If human review comments are present, keep `Final Status` as `Awaiting Re-review` or `Awaiting Sign-Off` until the updated artifacts are re-reviewed and signed.

| Round / Version | Reviewer / Source | Review Comment Summary | Affected Requirement Area / Artifact | Version Change / Closure Evidence | Status |
|----|----|----|----|----|----|
| Requirement consolidation v1 | QA1 | Drafted SSO requirement analysis from two PRD PDFs, prior login-registration SSO references, and local SP mock retrieval. | `02-analysis/requirement-consolidation-sso.md` | Generated formal v2.1 review markdown and paired DOCX. | Awaiting Sign-Off |
| Requirement review r1 | Test Manager / Product Owner | Reviewer answered Q-1..Q-15 in the DOCX. First-round execution is scoped to local mock SP `http://127.0.0.1:6080/login`; external SPs, WestK API contract testing, CRM sync details, QPS, AuthCode expiry, and APP WebView are excluded or ignored for this package. | SSO scope, integration boundary, open decisions, and test-design gate | Answers absorbed from `requirement-consolidation-sso.reviewed-raw-20260713-135609.docx`; final human sign-off captured on 2026/07/13. | Closed |
| Final sign-off | Test Manager / Product Owner | Requirement consolidation signed off for first-round SSO test design. | All reviewed requirement areas | Human sign-off date and signature captured in section 1; Open Review Comments synchronized to None; no Word comments remain in the paired DOCX. | Signed Off |

## 5. Scope Decision

| Scope Area | Decision | Evidence / Comment |
|----|----|----|
| Business capability | In Scope | AnTank becomes the unified C-end login, registration, and forgot-password entry; SP sites redirect to AnTank and establish local session after token exchange. |
| User roles and permissions | In Scope | Public visitor, registered user, old WestK Email user, mobile user, third-party OAuth user, and guest user paths must be considered. Admin provisioning itself is not full-scope unless Q-5/Q-8 expand it. |
| Data and configuration | In Scope / Deferred | For the first executable round, use local mock SP `http://127.0.0.1:6080/login` and available SIT configuration. WestK API contract details, client credentials for real external SPs, and CRM data configuration are not owned by this package unless later provided. |
| Integration or third party | In Scope / Deferred | OAuth authorize/token/checking/register/session-sync plus broadcast/logout are in scope against the local mock SP. WestK Customer Portal three-step API contract testing is owned by WestK IT and is not covered by this package. |
| Reporting, audit, or logs | In Scope | Security/audit requirements include PII masking, cross-system call audit, retry, and DLQ behavior at evidence-friendly validation level. |
| Non-functional, security, or compliance | In Scope / Deferred | Basic token/session/security behavior is in scope where observable through the mock SP. QPS/rate-limit and full platform security contract testing are ignored/deferred for this package per reviewer answers. |
| Regression impact | Covered after sign-off | Existing login-registration SSO cases are impact references. A dedicated `10-SSO/2026-07-13` case set must link regression impact after scope sign-off. |

## 6. Requirement Quality Decision

| Area | Decision | Evidence / Comment |
|----|----|----|
| Completeness | Pass with signed-scope constraints | Reviewer answered Q-1..Q-15 and narrowed first-round executable scope to local mock SP. Human sign-off date and signature are captured. |
| Correctness | Pass with assumptions | Extracted requirement facts align between business and technical PDFs; assumptions are separated under U-1..U-8. |
| Consistency with related modules | Pass | Prior login-registration SSO smoke cases are treated as references only, preventing accidental mutation of old case files. |
| Clarity and testability | Pass | Q-1..Q-15 are answered and signed off. Test design may proceed under the signed first-round scope. |
| Traceability | Pass | Sources, PRD pages/sections, prior packages, and optional local mock are listed and classified. |
| Dependencies and assumptions | Pass with scope limitation | Local mock SP is the executable SIT dependency. Real WestK API docs, external SP configs, and broader test accounts are outside first-round execution. |
| Risk acceptance | Pass | Reviewer accepted/ignored broadcast, logout, CRM sync, APP WebView, and performance/rate-limit risks for this package through signed Q answers. |

## 7. Review Findings

| ID | Severity | Finding | Owner | Resolution / Status |
|----|----|----|----|----|
| REQ-RV-SSO-001 | High | WestK `/initiate`, `/challenge`, and `/token` API details, authentication method, DEV/UAT URLs, and test accounts are required before old-user password login can be executable. | WestK IT / AnTank IT | Closed for this package scope - reviewer says WestK API contract/authentication is not owned by this package and only local mock SP is available for SIT. |
| REQ-RV-SSO-002 | High | SSO login broadcast and global logout are marked "待讨论"; test cases must not treat them as executable until signed in or explicitly deferred. | PM / Test Manager | Closed for this package scope - reviewer says broadcast and logout are executable through `http://127.0.0.1:6080/login`. |
| REQ-RV-SSO-003 | Medium | Password retention strategy for old WestK Email users changes long-term dependency on WestK Customer Portal API and affects regression design. | PM / Security / WestK IT | Closed for this package scope - reviewer selected option (a). |
| REQ-RV-SSO-004 | Medium | CRM sync behavior for no-email users, `antank_id`, and registration term b is not settled. | CRM owner / PM / Legal | Closed for this package scope - reviewer answered no-email CRM sync as ignore/skip, CRM `antank_id` as No, and term b as ignore. |
| REQ-RV-SSO-005 | Medium | No mindmap, Figma, or authenticated ZenTao story body is available in the package. | Test Manager / PM | Closed for this package scope - reviewer approved local mock SP as execution helper and did not require additional sources before test design. |

## 7A. Requirement Analysis Detail

### 7A.1 Source Authority

West Kowloon source authority is mindmap > PRD > Figma. This package currently has no mindmap and no Figma input, so the two PRD PDFs are the working source. Items explicitly marked "待确认" or "待讨论" are not final decisions and must be answered or marked Deferred.

### 7A.2 Integrated Breakdown

| ID | Capability | Trigger / Actor | Expected Outcome | Source |
|----|----|----|----|----|
| F1 | AnTank becomes the only customer-facing C-end login entry | User clicks login/register/forgot password from a WestK-family website. | User is redirected to AnTank instead of the old WestK Customer Portal login page. | Business PDF pages 2-4; design PDF sections 1.2, 1.3, 2 |
| F2 | Source site branding and language are carried into AnTank | SP starts login or registration with `source`, `redirect_uri`, and `lang`. | AnTank shows the corresponding brand and language context. | Business PDF page 6; design PDF section 4.2 |
| F3 | Existing WestK Email users authenticate without re-registration | A/B class old WestK Email user logs in with Email + password. | AnTank checks `westk_legacy_accounts`, calls WestK three-step API, creates/binds local account, and signs an AnTank session. | Business PDF pages 6-7, 10-12; design PDF sections 3.2, 5.1, 5.1.3 |
| F4 | Email OTP login is handled by AnTank for all Email users | Any Email user chooses Email OTP login. | AnTank sends and verifies OTP internally, then creates/finds the user and signs a session. | Business PDF page 6; design PDF sections 5.2 and 11.1 |
| F5 | New Email, mobile, third-party, and guest paths remain supported | C/D/E class users or guests authenticate through existing AnTank modes. | Email password, SMS OTP, third-party OAuth, and guest temporary session continue under the unified entry. | Business PDF pages 6 and 8; design PDF sections 4.1, 5.3, 5.4, 5.5 |
| F6 | SP sites complete OAuth authorization-code login through AnTank | SP starts OAuth flow and user authenticates at AnTank. | SP receives AuthCode, exchanges it at token endpoint, validates token/userInfo, and establishes local session. | Design PDF sections 6.1, 6.2, 6.4 |
| F7 | Silent SSO works when user is already logged in at AnTank | User has an existing AnTank session and enters SP login flow. | Checking API returns ExchangeCode and SP establishes local session without credential re-entry. | Design PDF section 6.2 |
| F8 | Multi-site SSO login broadcast is optional | AnTank authentication completes and broadcast is enabled. | AnTank pushes ExchangeCode to registered SP checkAuth URLs so other sites can establish sessions. | Business PDF pages 8 and 11-12; design PDF section 6.3 |
| F9 | Registration is centralized at AnTank and can return logged-in SP session | User clicks register from a SP site. | AnTank completes registration, returns ExchangeCode, and SP establishes local session. | Business PDF page 8; design PDF section 8 |
| F10 | Global SSO logout is optional | User clicks logout from a SP site and global logout is enabled. | SP invokes `/SingleSignOut`; AnTank revokes session and notifies registered SPs to clear sessions. | Business PDF pages 8 and 11-12; design PDF section 7 |
| F11 | SP sites may call Session Sync | SP needs to extend or synchronize active session state. | SP calls `/s/user-session-sync`; recommended frequency is at most once per 12 hours. | Design PDF section 10.3 and checklist |
| F12 | Registration-triggered CRM sync is limited and partly pending | User registers with optional term b or purchases/renews membership. | AnTank asynchronously pushes basic user/member info where applicable; deep CRM integration is out of this SSO flow. | Business PDF page 9; design PDF sections 8.2, 10 |
| F13 | SP configuration and callback setup are prerequisites | A SP is onboarded. | SP has client credentials, redirect URI whitelist, source Channel Name, and optional checkAuth URL. | Business PDF pages 10-12; design PDF sections 6.5, 11.2, 12 |
| F14 | Security controls apply to cross-system calls | AnTank and WestK/SP systems call backend APIs. | HTTPS, client auth, JWT, signing, nonce replay protection, PII encryption, audit masking, retry, and DLQ apply where relevant. | Business PDF page 9; design PDF section 9 |
| F15 | Migration table and identity mapping support first login | Old WestK Email user logs in for first time after migration. | `westk_legacy_accounts`, `openmember`, and `member` identity mapping are updated for later login/session use. | Business PDF page 7; design PDF sections 3.2, 5.1.3, Appendix C |

### 7A.3 Differences

| ID | Type | Capability | Previous / Adjacent Behavior | New Requirement | Source |
|----|----|----|----|----|----|
| D-prev-1 | Previous adjacent package | F6/F7 | `01-login-registration/2026-06-16` had SSO smoke and three-jump cases pending/NA due to missing SSO environment. | `10-SSO/2026-07-13` defines full IdP/SP OAuth flow, Checking API, token exchange, ExchangeCode, and SP local session behavior. | AUTH-014, AUTH-039..041; design PDF sections 6.1-6.2 |
| D-prev-2 | Previous adjacent package | F1 | Prior login-registration cases treated SSO as adjacent to website login. | New package makes AnTank the only customer-facing login/register/forgot-password entry for WestK-family sites. | Business PDF pages 2-4 |
| D-prev-3 | Previous adjacent package | F3/F15 | Prior package did not define old WestK Email migration mechanics. | New package adds migration table, WestK three-step password authentication, and identity binding. | Design PDF sections 3.2 and 5.1 |
| D-std-1 | Prior design direction | F1/F6 | Earlier OIDC/silent-SSO directions kept dual login entries or custom silent SSO. | This requirement cancels WestK C-end login page and centralizes login at AnTank. | Design PDF pages 1-3 and Appendix A |
| D-adj-1 | Adjacent module | Login and Registration | Existing auth flows were designed under login-registration scope. | Those flows must now operate through unified AnTank entry and SP callback context. | Current package PRDs |
| D-adj-2 | Adjacent module | Website shell / header | Login/register/logout links were local or existing-page driven. | Links need SSO redirect/checking/logout behavior. | Current package PRDs |
| D-adj-3 | Adjacent module | CRM / Membership | Membership data existed outside this SSO package. | Old user migration and optional registration sync affect membership tier, expiry, offers, and identity mapping. | Current package PRDs |

### 7A.4 Proposed Test Scope After Sign-off

| Capability | Scope Statement | Rationale |
|----|----|----|
| F1/F2 | SP login/register entry redirects to AnTank with correct `source`, `redirect_uri`, and `lang`; AnTank displays expected brand/language context. | Direct user-facing change and SP prerequisite. |
| F3/F15 | Old WestK Email password login through migration table and WestK three-step API, including first-login account creation/binding and repeat-login behavior. | Core compatibility promise for old Email users. |
| F4/F5 | Email OTP, new Email password, mobile OTP, third-party OAuth, and guest paths remain available through unified entry, with SP callback smoke. | Existing auth methods must not regress. |
| F6 | Authorization-code callback and token exchange, including one-time code behavior, JWT/userInfo validation, and SP local session creation. | Core IdP/SP integration behavior. |
| F7 | Silent SSO Checking API behavior for already-logged-in and not-logged-in users. | Required for "no repeated login" experience. |
| F8 | Login broadcast if signed in; otherwise Deferred cases only. | Source marks this as pending decision. |
| F9/F12 | Centralized registration, redirect back to SP, local session establishment, and term-b/CRM sync behavior according to sign-off decision. | User-facing registration and data-sync risk. |
| F10 | Global logout if signed in; otherwise Deferred cases only. | Source marks this as pending decision. |
| F11 | Session sync endpoint smoke and basic frequency/authorization validation. | Endpoint is part of implementation checklist. |
| F13/F14 | Configuration and security negative checks: redirect URI whitelist, client authentication, expired/reused code, invalid signature/nonce, token expiry, and PII masking. | High integration/security risk. |

### 7A.5 Deferred Or Handled Elsewhere By Default

| Capability | Default Treatment | Reason |
|----|----|----|
| Full CRM deep integration, points, D365 mapping, and bidirectional sync | Deferred / separate CRM package | PRD says deep CRM integration is outside this SSO flow. |
| Full order-query behavior `AT-ORDER-01` | Handled elsewhere | Mentioned in PRD but not core login/SSO. |
| APP WebView login-state transfer | Deferred unless Q-15 expands scope | PRD marks APP WebView as later confirmation. |
| Full performance/load testing for event-sale login peak | Deferred performance plan | QPS/rate limit not confirmed. |
| Complete admin/secret-management CRUD | Platform/admin owner | This package can verify prerequisites, not own full provisioning lifecycle unless signed in. |
| Figma-specific UI layout validation | Deferred | No Figma source is present. |
| Existing auth field-level validation | Login-registration module | This package covers SSO integration smoke/regression, not full re-enumeration of old auth validation. |

### 7A.6 Unclear Items

| ID | Source Location | Ambiguity | Working Assumption |
|----|----|----|----|
| U-1 | Package source set | No mindmap and no Figma are present. | The two PRD PDFs are the working source until a mindmap or Figma source is added. |
| U-2 | ZenTao story 4305 | Only the URL is captured; authenticated story body is not exported. | Do not rely on live ZenTao body until it is exported into `01-input`. |
| U-3 | Business PDF page 1 and design PDF appendix | Version/date labels differ slightly (`v1.0`, `v1.1`, 2026-06-16/17). | Treat both PDFs as the same 2026-06-17 draft requirement package unless PM says otherwise. |
| U-4 | Business/design PDFs | Several areas are explicitly marked "待讨论" or "待确认". | Author Deferred cases after sign-off only for items still not decided. |
| U-5 | Design PDF Appendix B | DEV/UAT/PROD endpoints are named, but service readiness is not proven. | Test design should require environment URLs and test accounts as preconditions. |
| U-6 | Design PDF section 6.4 | Token response sample lists `expires_in` as a timestamp-like value rather than a duration. | Verify actual API contract before asserting expiry semantics. |
| U-7 | Business PDF page 6 / design PDF section 5.4 | Mobile users are supported, but HK/mobile execution constraints may apply. | Author cases and mark HK-side / sandbox prerequisites if mainland QA cannot execute. |
| U-8 | Business/design PDFs | It is not explicit whether AnTank ticketing site must be tested as a SP in this package or only as IdP/native site. | Include AnTank ticketing as SP-compatible smoke unless Test Manager limits scope to external SPs only. |

### 7A.7 Items Requiring User Confirmation

| ID | Question | Options | Owner | Signed-off answer |
|----|----|----|----|----|
| Q-1 | Is this package a new dedicated SSO package rather than an update to `01-login-registration/2026-06-16`? | (a) Yes, create dedicated `10-SSO/2026-07-13` test cases and link old AUTH cases as references / (b) reopen old login-registration cases / (c) split: integration cases here, UI auth cases in old package | Test Manager | a. Reviewer will manually sync into Login/Registration if needed. |
| Q-2 | Which SP sites are in first-round execution scope? | (a) WestK + myWestK only / (b) WestK + myWestK + M+ + HKPM / (c) include AnTank ticketing as SP-compatible smoke too | Test Manager / PM | Local mock SP `http://127.0.0.1:6080/login` is treated as WestK page. Other SPs can be omitted. |
| Q-3 | Is SSO login broadcast in scope for this round? | (a) Yes, executable / (b) No, out of scope / (c) Author Deferred cases until SP callback URLs are ready | PM / Test Manager | a. Yes; `http://127.0.0.1:6080/login` is executable. |
| Q-4 | Is global SSO logout in scope for this round? | (a) Yes, executable / (b) No, out of scope / (c) Author Deferred cases until product confirms priority | PM / Test Manager | a. Yes; `http://127.0.0.1:6080/login` is executable. |
| Q-5 | Who owns full WestK Customer Portal three-step API contract testing? | (a) WestK IT owns full contract; this package tests AnTank integration result / (b) this package owns API contract tests too / (c) split API contract under platform package | Test Manager / WestK IT | a. This package does not need to cover it. |
| Q-6 | What is the confirmed backend authentication method for AnTank calling WestK APIs? | (a) client_id/client_secret / (b) mutual TLS / (c) signed JWT/client credentials / (d) other | WestK IT / AnTank IT | a. This package does not need to cover it. |
| Q-7 | Should AnTank retain password hash after successful old-user password verification? | (a) Retain hash for later local verification / (b) Do not retain; call WestK every time / (c) retain only after explicit user reset/change password | PM / Security / WestK IT | a. |
| Q-8 | Are DEV/UAT URLs, client credentials, redirect URI whitelist, and test accounts ready for execution? | (a) Ready and will be attached / (b) not ready, author cases as Deferred / (c) partial readiness by SP/site | WestK IT / AnTank IT | Only `http://127.0.0.1:6080/login` is available as SIT test target. |
| Q-9 | What should happen for no-email mobile or third-party users when CRM sync is needed? | (a) skip CRM sync / (b) require email completion / (c) create CRM placeholder / (d) not in this package | PM / CRM owner | a. Ignore/skip. |
| Q-10 | Should CRM store `antank_id` for long-term account mapping? | (a) Yes / (b) No / (c) TBD outside SSO package | CRM owner / WestK IT | b. |
| Q-11 | Is term b ("also register as WestK member / sync personal information to CRM") retained? | (a) Retain and test / (b) remove from registration / (c) display only for selected user types | PM / Legal / CRM owner | Ignore. |
| Q-12 | What are AuthCode and ExchangeCode expiry and reuse rules? | (a) 15 minutes, one-time use / (b) different value from API spec / (c) TBD, author Deferred cases | SP dev teams / AnTank IT | Ignore. |
| Q-13 | What is the expected QPS/rate limit for WestK three-step password APIs during ticket-sale peaks? | (a) confirmed limits available / (b) no limits but monitor / (c) performance package needed before release | WestK IT / Performance owner | Ignore. |
| Q-14 | Should local `westk-consumer-sso-sp-mock` be an approved execution helper for SIT? | (a) Yes, use it for early SP flow testing / (b) no, only real SP sites count / (c) use mock for debug only, not pass/fail evidence | Test Manager / Dev | a. |
| Q-15 | Should APP WebView be included in this package? | (a) No, defer / (b) author Deferred placeholder only / (c) include executable WebView cases | PM / App team / Test Manager | a. |

## 8. Conditions and Next Step

| Item | Value |
|----|----|
| Conditions for Sign-off | Met. Q-1..Q-15 answers are captured and human sign-off date/signature are provided. |
| Open Review Comments | None |
| Required Follow-up | Proceed to `03-test-design` using the signed first-round scope. |
| Next Folder / Phase | `03-test-design` |
| Handoff Decision | Proceed to `03-test-design`; generate SSO test cases under the signed scope. |
