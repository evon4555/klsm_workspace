# Requirement Risk Review

---

## [SECTION] Revision History

| Date | Reviewer | Change |
|---|---|---|
| 2026-05-13 | AI QA draft | Initial draft based on figma-link.md and extracted PRD text. Mindmap not opened (explicit v1 note). |
| 2026-05-15 | AI QA reviewer | Captured mindmap registration/login sub-tree and cross-checked PRDs. Resolved source authority for this project (mindmap > PRD; PRD-only items still in scope). Closed PRD/mindmap-confirmed open items; reopened mindmap-revealed questions; added captcha-across-flows, two-login-mode, email-link, error-permutation, auto-OTP-registration, WestK SSO three-jump, forgot-password specifics, and HK-mobile deferred-verification handling. |

---

## [SECTION] Requirement Summary

- Business goal: Provide website users with account registration, registered account login, third-party co-branded login, guest login, password recovery, and privacy consent controls before using ticketing services.
- Main change: Trial run scope is limited to Website registration and login. Other website functions (News Centre, ticketing, wallet, etc.) are excluded from this phase 7 dry run.
- Affected users: Public visitors, registered website users, guest users, users authenticating through third-party providers, and users entering ticket purchase from an authenticated state.
- Affected systems: Website frontend, WestK Account / SSO, account service, image-captcha service (动态码), email OTP service, third-party identity providers (Google, Facebook, X, Tiktok, wechat), privacy policy page, session management, shopping cart and order eligibility rules.
- Source basis: Mindmap registration/login sub-tree (`..\01-input\02-mindmap\2026-05-26\{注册,登录1,登录2,忘记密码}.png`) is the authoritative source; Website-level PRDs at `..\..\..\..\..\01-source-documents\02-prd\` are supporting reference; `..\01-input\01-figma\figma-link.md` and project context supplement. Source-authority order for this project: **mindmap > PRD**. Mindmap-only items (e.g., 忘记密码) are in scope. PRD-only items are also in scope (PRD-fills-gap rule, per user direction 2026-05-15).

---

## [SECTION] Resolved Questions (Closed Since v1)

| Source That Resolved | v1 Question | Resolution |
|---|---|---|
| Mindmap | Which third-party providers are in MVP scope? | **Five providers (confirmed):** Google, Facebook, X, Tiktok, wechat. (Apple removed from v1 assumption.) |
| Mindmap | Is forgot password formally in scope or only in Figma? | **In scope.** Mindmap has an explicit 忘记密码 branch annotated "PRD上没有写", confirming intentional inclusion. |
| User direction (2026-05-15) | Does the mindmap label "只支持邮箱" mean mobile is out of scope? | **No.** Label is to be ignored. Mobile registration and mobile login are yellow-placeholder branches: in scope, not yet detailed. Cases marked "Deferred — HK-side verification" (mainland team cannot test HK mobile). |
| PRD 在线购票 §3.2.1 (PRD-fills-gap) | Does first-time OTP login auto-create an account? | **Yes.** Auto-registration is part of OTP login flow. |
| PRD 在线购票 §3.2.3 (PRD-fills-gap) | Does guest mode show a 5-min-remaining popup countdown? | **Yes.** |
| PRD 在线购票 §3.2.4 (PRD-fills-gap) | Are there three SSO jump scenarios? | **Yes** — BU-logged-in jump / BU-not-logged-in jump / direct visit. (Note: overall SSO scope is marked 待讨论 at PRD level — see Open Questions.) |
| Mindmap | What does the verification mechanism look like for native registration? | Image-captcha (动态码) + email OTP. No SMS in current mindmap registration scope. |

---

## [SECTION] Open Questions

| Priority | Question | Why It Matters | Owner | Source |
|---|---|---|---|---|
| High | Field-level rules: password complexity, captcha image format, OTP digit count, OTP validity, captcha validity, email-link expiry. | Test data and expected validation messages cannot be finalized. | Product / Tech | Mindmap "?" placeholders |
| High | Login session validity in password mode and OTP mode — exact expiry value? | Session expiry and auto-logout cases depend on this. | Product / Tech | Mindmap "登录过期时间?" |
| High | Guest session validity calculation: from last action, or from login start? | Determines guest timeout test design. | Product / Tech | Mindmap explicit "?" |
| High | Guest robot-verification failure: which page does the user land on? | Determines guest negative-flow expected result. | Product | Mindmap explicit "?" |
| High | OTP login mode: is password required in addition to OTP? Mindmap lists "邮箱 + 密码 + 动态码 + 验证码", but conventional OTP login uses no password. | Determines OTP-login credential combinations and negative matrix. | Product / Tech | Mindmap ambiguous |
| High | Failed-login lockout threshold and lock duration. | Security lockout case cannot be executed deterministically. | Product / Tech | v1 carried |
| High | WestK SSO scope decision (PRD §3.2.4 marked 待讨论): include three jump scenarios in this dry-run or defer? | Determines whether to execute SSO cases now. | Product / Tech | PRD 待讨论 |
| Medium | Forgot password: send temporary password vs reset-token URL? Does login post-reset force or guide password change? | Determines forgot-password flow steps. | Product | Mindmap "发送零时密码?" / "登录有引导修改密码?" |
| Medium | Third-party login: after authenticating via provider, does sharing flow auto-login the user on the corresponding partner site? | Determines third-party integration scope. | Product / Tech | Mindmap "?" |
| Medium | Captcha exact behavior: auto-refresh on wrong input vs click-to-refresh only; binding of captcha to OTP request. | Captcha negative cases need exact behavior. | Product / Tech | Mindmap "输错后自动刷新?" |
| Medium | Multilingual scope: which languages must be validated for this dry-run? | Compatibility / message scope. | Product | v1 carried |
| Low | Analytics, audit, and security logs for registration and login failures. | Useful for ops investigation; not always visible to functional QA. | Tech / Ops | v1 carried |

---

## [SECTION] Risk Review

| Risk Area | Risk | Impact | Suggested Test Focus |
|---|---|---|---|
| Business | Users cannot register or login before purchasing tickets. | Revenue flow and account-based services are blocked. | P0 native registration, password login, OTP login, third-party login, guest login smoke coverage. |
| Authentication mode confusion | Two login modes (password / OTP) may be confused at UI or backend, allowing wrong credential combinations or blocking valid ones. | Users authenticate without all required factors, or are blocked by stricter-than-spec rules. | Distinct cases for password mode (邮箱+密码+动态码) and OTP mode (邮箱+OTP+动态码, with password ambiguity per Open Question); negative combinations for each. |
| Data | Duplicate accounts may be created across native registration, OTP auto-registration, and third-party login. | Identity, wallet, orders, coupons, membership benefits split or exposed incorrectly. | Existing-user linking, new-user creation, duplicate email, missing provider profile data, OTP auto-registration on first OTP login, third-party-to-existing-account merge behavior. |
| Permission | Guest users may access registered-user personal centre, wallet, or order management. | Privacy and entitlement leakage. | Guest access restrictions, registered-only entry checks. |
| Integration | WestK Account SSO and third-party providers may fail or return partial data. | Login loops, failed account association, wrong identity. | SSO three-jump scenarios (BU-logged-in / BU-not-logged-in / direct); provider cancel/error; provider profile mapping for 5 providers (Google / Facebook / X / Tiktok / wechat). |
| Anti-abuse (captcha) | Image-captcha (动态码) controls are present across registration, password login, OTP login, and forgot password; weak validation or predictable refresh could enable scripted abuse. | Brute force on credentials, OTP harvesting, account enumeration via forgot-password. | Captcha required on each flow; auto-refresh on wrong input; click-to-refresh; captcha bound to its image; replay rejection. |
| Email OTP integrity | OTP not invalidated on resend, OTP reused, OTP leaked via per-language email tampering, or replay via email-embedded link. | Account takeover. | 60s anti-resubmit; resend invalidates previous; OTP single-use; per-language OTP email correctness; expired-link rejection. |
| Email-link registration alternative | Registration completion via clicked link in email is an alternative path with distinct failure modes (link expiry, navigation to wrong page, replay). | Inconsistent account creation; replay creates account without re-captcha. | Successful link returns to pre-entry page; expired link returns to registration page; replayed link rejected; link respects expiry duration. |
| Compatibility | Authentication forms may break on mobile browsers or across languages. | High customer-facing friction at entry point. | Desktop/mobile responsive layout, keyboard behavior, browser compatibility, multilingual messages. |
| Performance | Captcha refresh, OTP send, SSO, or third-party callbacks may be slow. | Users abandon flow or create duplicate submissions. | Loading state, duplicate-click prevention, timeout handling. |
| Security | Weak password rules, brute force, OTP abuse, missing privacy consent, insecure session handling. | Account takeover, compliance risk, personal data exposure. | Password policy, failed-attempt lockout, OTP expiry/resend limits, privacy checkbox enforcement, logout/session expiry, sensitive data not in browser history post-logout. |
| Regression | Authentication state affects cart, inventory lock, personal centre, wallet, order management, and checkout privacy terms. | Downstream ticketing flows behave differently for registered vs guest users. | Regression probes for cart eligibility, personal centre access, guest order visibility, checkout handoff. |
| Operations | Lack of audit logs for login failures and account lock events. | Hard to investigate customer support and security incidents. | Confirm audit/log requirements; validate accessibility in SIT. |
| Forgot password (mindmap-only) | Reset flow is in mindmap but not in PRD; engineering implementation likely under-specified. | Inconsistent or insecure reset implementation. | Mindmap-described flow (邮箱 → OTP → 动态码 → password change); negative paths (unknown email, expired OTP, replay, weak new password). |
| Mobile flows (yellow placeholder) | Mobile registration and mobile login exist in mindmap as placeholders, not yet detailed. | Late-stage scope expansion risk; incomplete authentication coverage if mobile becomes required. | Author placeholder cases; mark "Deferred — HK-side verification" until detail is provided. |
| Error message localization | Mindmap repeatedly notes "多语言" on error and page-hint nodes; UI may show fallback English/Chinese in some locales. | Customer-facing message quality fail; possible compliance issue for regulated wording. | Sample each error scenario in each supported locale; validation messages, OTP email content, page hints, privacy wording. |

---

## [SECTION] Edge Cases And Negative Scenarios

**Registration**:
- Empty mandatory fields.
- Invalid email format; duplicate email (registered) → existing-account message and login guidance.
- Password rule violations; two-password-input mismatch; show/hide plaintext toggle behavior.
- Captcha (动态码) missing, wrong, expired; auto-refresh on wrong input; click image to refresh; captcha must match its image.
- Email OTP wrong, expired, replayed; resent within 60s rejected; resent invalidates previous; OTP digit-count rule.
- Verification email — per-language content; correct format, sender, subject; both OTP and link options present.
- Email link option: clicked valid link → success + redirect to pre-registration page; clicked expired link → return to registration page; link respects "Link 失效时间".
- Privacy policy not consented → submission blocked.
- Multilingual: error messages, page hints, OTP email all localized.
- Registration success → return to the page the user came from (not generic home).
- Mobile registration (yellow placeholder) — defer to HK-side verification.

**Login — password mode**:
- Wrong email; wrong password; wrong captcha; combinations of any one wrong / any two wrong / all wrong (each with distinct localized message).
- Repeated failed login reaches configured lock threshold (threshold TBD).
- Session expiry value TBD → auto-logout when expired.
- Active logout clears session; back-button cannot resurrect authenticated pages.

**Login — OTP mode**:
- Wrong email / wrong OTP / wrong captcha (confirm whether password also required per Open Question).
- First-time OTP login auto-creates an account (PRD §3.2.1).
- OTP expiry, resend cooldown, resend invalidates previous.
- One-wrong / two-wrong / three-wrong / all-wrong combination messages.

**Login — guest**:
- Robot verification pass → guest session active; verification fail → land on TBD page.
- Session expiry (from login start vs last action — TBD) → expiry clears cart, order draft, filled information.
- 5-minute-remaining popup countdown warning (PRD §3.2.3) — popup appears, dismissible, countdown continues.
- Active logout clears guest data.
- Guest blocked from personal centre, wallet, order management, coupons, membership, favourites.

**Login — third-party**:
- Successful login via each of the 5 providers (Google, Facebook, X, Tiktok, wechat) for new and existing users.
- Provider authorization cancelled at provider page.
- Provider returns missing or no usable identifier.
- First-time third-party login still requires email-registration step; subsequent logins do not.
- Sharing-on-provider auto-login behavior (TBD per Open Question).

**Login — WestK SSO (PRD §3.2.4, status 待讨论)**:
- User already logged into another West Kowloon BU site → click to ticketing → identity auto-synced, no re-login.
- User not logged into any West Kowloon BU site → click to ticketing → goes through normal login flow.
- User directly visits ticketing → registration or login as usual.

**Forgot password**:
- Registered email → reset triggered (temporary password vs token-link — TBD); login post-reset prompts password change (TBD).
- Unregistered email → clear error.
- OTP wrong / expired / replayed / resent within 60s.
- Captcha required and validated.
- New password fails password rules.

**Session and post-login**:
- Registered user logout clears authenticated state.
- Session expiry during checkout redirects safely; sensitive data not in browser history.
- Browser back-button cannot resurrect authenticated pages.

---

## [SECTION] Recommendation

- Requirement readiness: **Needs Clarification** (12 Open Questions, mostly thresholds / TBDs and SSO scope decision).
- Recommended risk level: **High**.
- Next action:
  1. Resolve High-priority Open Questions before manual execution: session expiry values, OTP-mode credentials, third-party provider sandbox setup, captcha exact rules, OTP digit count and validity, lockout thresholds, SSO dry-run scope decision.
  2. Treat HK-mobile-related and SSO three-jump cases as conditional: author them now, mark "Deferred — pending product decision / HK-side verification" until inputs are firm.
  3. Proceed with test case authoring and execution for non-blocked items.
