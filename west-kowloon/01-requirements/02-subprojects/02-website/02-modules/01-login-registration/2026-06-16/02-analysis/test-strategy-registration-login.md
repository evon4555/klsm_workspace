# Test Strategy

---

## [SECTION] Basic Information

- Project: West Kowloon Website
- Feature / Release: 2026-05 dry run - Website registration and login
- Requirement Link: 01-input/01-figma/figma-link.md; project functional specification Website section REQ-WEB-REG-001 to REQ-WEB-REG-006
- Version / Build: TBD
- Owner: Antank QA Team
- Reviewers: Product / BA / Tech Lead / QA Lead
- Date: 2026-05-14
- Risk Level: High

---

## [SECTION] Business Context

### [FIELD] Business Goal

Enable visitors and registered users to enter the Website ticketing journey through native registration, registered login, co-branded third-party login, or guest login while enforcing privacy consent and secure identity handling.

### [FIELD] User Impact

The feature affects all website users before account-based ticket purchase, personal centre, wallet, order management, and guest checkout behavior.

### [FIELD] Critical Business Flows

- Flow 1: Visitor completes native registration after required information, verification, and privacy consent.
- Flow 2: Registered user logs in with official ticketing website account and receives correct SSO identity state.
- Flow 3: Visitor logs in through third-party provider as either a new user or existing associated user.
- Flow 4: Visitor uses guest login after non-robot verification and is constrained by guest validity and limited permissions.
- Flow 5: User recovers account access through forgot password / reset password if this flow is in release scope.

---

## [SECTION] Test Scope

### [FIELD] In Scope

- Native account registration.
- Privacy policy checkbox and link behavior during registration.
- Registered account login and logout.
- Forgot password / reset password draft coverage, conditional on product confirmation.
- WestK Account SSO synchronization at login state level.
- Third-party co-branded login for new and existing users.
- Guest login, guest validity countdown, guest logout, and guest timeout behavior.
- Form validation, error messaging, loading states, duplicate submission prevention.
- Registered vs guest permission checks for personal centre, order management, wallet, coupons, membership, favourites.
- Desktop and mobile browser sanity checks for authentication screens.

### [FIELD] Out Of Scope

- News Centre.
- Full event browsing, ticket purchase, payment, wallet, order management, and personal centre feature testing except authentication-state regression probes.
- Backend admin account management.
- Full provider-by-provider certification testing unless provider credentials and sandbox are provided.
- Production monitoring validation.

### [FIELD] Assumptions

- The website has only registration/login functions for this trial.
- Mindmap is intentionally not used until after the first draft is complete.
- Figma MCP is currently rate-limited; figma-link.md scope is treated as the Figma source summary.
- PDF text extraction tooling is unavailable in this environment; project-level functional specification text was extracted from DOCX where possible.
- Guest mode validity is 10 minutes by default and globally configurable, per functional specification.
- Registered website login should synchronize with WestK Account SSO, per functional specification.

### [FIELD] Dependencies

- Product: Field-level rules, provider list, forgot-password release decision, guest behavior confirmation.
- Design: Final Figma screens and responsive variants for login/register/reset/guest/third-party login.
- Development: SIT build with auth, SSO, verification, and provider callback endpoints.
- Data: Registered active account, locked/disabled account, duplicate email/mobile, third-party sandbox users, guest session data.
- Environment: SIT website URL, WestK Account test endpoint, provider sandbox callback configuration.
- Third-party service: Non-robot verification, OTP/email/SMS service if applicable, WeChat, Douyin, Facebook, X, Google providers as scoped.

---

## [SECTION] Risk Analysis

| Risk Area | Risk Description | Impact | Mitigation | Owner |
|---|---|---|---|---|
| Business | Users fail to authenticate before ticket purchase. | Ticketing conversion blocked. | P0 smoke for all supported entry methods. | QA |
| Data | Native and third-party accounts create duplicates. | Orders, wallet, membership, coupons may attach to wrong identity. | Existing-user linking and duplicate data tests. | QA / Tech |
| Permission | Guest sees registered-only pages. | Privacy and entitlement leakage. | Guest restriction regression probes. | QA |
| Integration | SSO or provider callback fails. | Login loop or wrong identity. | Provider success/cancel/error and SSO sync tests. | QA / Tech |
| Compatibility | Form layout or validation unusable on mobile. | Customer friction. | Mobile Chrome/Safari sanity checks. | QA |
| Performance | Verification or callback is slow. | Duplicate submissions and abandoned login. | Loading, timeout, retry, duplicate-click tests. | QA / Tech |
| Security | Weak auth controls, OTP abuse, privacy consent bypass. | Account takeover or compliance defect. | Security checklist for password, lockout, consent, session expiry. | QA / Security |
| Regression | Auth state breaks cart, guest checkout, personal centre, wallet, and order visibility. | Downstream ticketing defects. | Minimal cross-module probes by user state. | QA |

---

## [SECTION] Test Types

| Test Type | Required | Scope | Owner | Evidence |
|---|---|---|---|---|
| Functional | Yes | Main and negative flows for registration, login, guest login, third-party login, forgot/reset if confirmed. | Functional QA | Screenshots for P0/P1, execution notes. |
| Regression | Yes | Auth state handoff to personal centre, wallet/order restrictions, guest cart cleanup, checkout entry. | Functional QA | Screenshots and state notes. |
| API | Conditional | Auth, SSO, OTP, account linking, guest session endpoints if API docs or logs are available. | QA / Tech | Request/response logs with sensitive data masked. |
| UI | Yes | Figma-aligned fields, validation messages, privacy link, loading states, responsive behavior. | Functional QA | Screenshots for desktop and mobile key screens. |
| Compatibility | Yes | Latest Chrome, Edge, Safari mobile or emulated mobile; final matrix TBD. | Functional QA | Browser/version notes. |
| Performance | Light | Login/register callback response and duplicate-click resilience; no full load test in this trial. | QA / Tech | Timing notes where measurable. |
| Security | Yes | Password policy, failed login lock, privacy consent, session/logout, OTP limits. | QA / Security | Screenshots/logs with secrets masked. |
| Automation | Candidate | Stable smoke cases for native login, privacy consent, guest login, and registered-only access restriction. | Automation QA | Automation candidate list, not mandatory for dry run. |

---

## [SECTION] Test Environment And Data

### [FIELD] Environment

- Environment Name: SIT
- URL / Endpoint: TBD
- Version / Build: TBD
- Configuration Notes: Provider sandbox, verification service, SSO test tenant, and guest validity configuration must be known before execution.

### [FIELD] Test Data

- Required data: New email/mobile, duplicate email/mobile, active registered account, locked account, disabled account, provider new-user account, provider existing-user account, guest session.
- Data owner: QA with Tech support.
- Data preparation method: Seed accounts through backend or registration flow; configure provider sandbox accounts; prepare privacy policy target page.
- Data cleanup method: Remove trial accounts where allowed; reset lockout state; expire guest sessions; clear browser cookies and local storage between user-state tests.

---

## [SECTION] Entry Criteria

- [ ] Requirement is clear enough for testing.
- [ ] Open questions are recorded.
- [ ] Test environment is available.
- [ ] Required test data is available.
- [ ] Test scope is agreed.
- [ ] Major risks are documented.
- [ ] Provider sandbox and callback URLs are configured.
- [ ] Privacy policy page target is available.

---

## [SECTION] Exit Criteria

- [ ] Required P0/P1 test cases are executed.
- [ ] Critical and high severity defects are resolved or accepted.
- [ ] Regression scope is executed.
- [ ] Evidence is attached or linked.
- [ ] Remaining risks are documented.
- [ ] Test report is completed.
- [ ] Release recommendation is stated.

---

## [SECTION] Release Risk And Recommendation

### [FIELD] Known Risks

- Field-level validation and password rules are not yet confirmed.
- Provider-specific availability is not yet confirmed.
- Forgot password / reset password source baseline is Figma scope only until product confirms.
- Figma MCP access is rate-limited, so detailed UI parity cannot be validated in this pass.

### [FIELD] Recommendation

Proceed With Risk

### [FIELD] Reason

- The trial can proceed for QA workflow validation and draft test design.
- Manual execution should not start until field rules, environment, provider list, and failed-login lock behavior are confirmed.
