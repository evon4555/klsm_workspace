# Test Case Review

---

## [SECTION] Basic Information

- Review ID: TCR-WEB-AUTH-20260517
- Project: West Kowloon Website
- Feature: Registration and login (2026-05 dry-run scope)
- Requirement Link: `..\01-input\input-index.md`; REQ-WEB-REG-001..006; mindmap registration/login sub-tree; PRD `在线购票.pdf` §3
- Test Case Set: `..\03-test-design\test-cases-registration-login.md`; `..\03-test-design\test-cases-registration-login.xlsx` (71 cases)
- Author: AI QA (QA2 role)
- Reviewer: AI QA (QA2 role) — pending human senior-QA co-sign before binding
- Review Date: 2026-05-17 (round 1); 2026-05-17 round 2 (re-review of QA1 revision); 2026-05-17 Quality Owner scope override
- Review Result: **Pass (AI re-review, scope-adjusted)** — 4 of 5 Majors Closed + 1 Removed (scope decision); 1 of 4 Minors Closed + 1 Removed (scope decision) + 2 Carried as low-priority follow-up. Final case count: 73.

---

## [SECTION] Revision History

| Date | Reviewer | Change |
|---|---|---|
| 2026-05-14 | AI QA reviewer (draft, not QA2-signed) | Initial review of the first 28 cases. Result: Needs Revision (6 Major + 1 Minor). **Stale** — the test case set has since grown to 71 cases through 4 revision rounds; that review is no longer descriptive of the current artifact. Superseded by 2026-05-17. |
| 2026-05-17 | AI QA (QA2 role) — round 1 | Full re-review against current 71 cases (post-mindmap-coverage closure). Carries forward 4 v1 Majors that remain blocked on product input (field rules, provider sandboxes, SSO scope decision, lockout thresholds — now expressed in the case set as explicit Deferred cases 011 / 039–041 / 059–063 / 064–071 rather than as gaps). Adds 5 new Major findings around mobile placeholders, auto-OTP-registration duplicate-blocking assumption, multi-device / concurrent session behavior, email-enumeration wording symmetry, and password-policy enumeration. Adds 4 Minor findings. |
| 2026-05-17 | AI QA (QA2 role) — round 2 | Re-review of QA1's 2026-05-17 revision (case set now 75 rows). Verified each round-1 finding against the revised md + regenerated xlsx. **All 5 Majors Closed**: TC-046/047 marked DO NOT EXECUTE with `Blocked` handoff guidance; TC-035 expected-result item 3 rephrased as conditional + yellow-celled (col 11); TC-072 (multi-device session) added Deferred + yellow row; TC-073 (enumeration parity) added; TC-074 (password policy enumeration) added Deferred + yellow row. **2 of 4 Minors Closed**: TC-075 (network-failure resilience) added; remaining 2 Minors (TC-058 sender condition; TC-001–028 coarse `Collected from` traces) carried as low-priority follow-up — TC-058 fix requires product input on sender-localization policy, coarse traces are polish that doesn't block execution. Result: **Pass (AI re-review)** — awaiting human senior-QA co-sign. |
| 2026-05-17 | Quality Owner (user) — scope override | Removed TC-073 (email-enumeration response parity) and TC-075 (transient network failure resilience). Rationale: both belong in dedicated security / resilience passes rather than the functional auth case set; including them dilutes dry-run focus. QA2 review findings #4 (Major) and #7 (Minor) re-classified as **Removed (scope decision)** rather than Closed. IDs 073 and 075 left as gaps. Case count: 75 → 73. |

---

## [SECTION] Review Summary

### [FIELD] Overall Assessment

The case set has matured substantially since v1. Mindmap-to-case coverage is now traceable leaf-by-leaf (8 explicit Deferred cases 064–071 + yellow-cell annotations on 015 / 022 / 030 / 034); the four major v1 ambiguity flags (provider list, OTP-mode credentials, captcha rules, SSO scope) have been converted from "unknown → blocking" to "captured as Deferred with prerequisite assumptions stated", which is the correct QA2 handling when product input is pending.

For phase 7 dry-run **drafting**, the set is sufficient. For **execution**, the set is not yet ready because:

1. A handful of in-scope behaviors are not yet covered (concurrent session, email-enumeration symmetry, password-policy enumeration, mid-flow network failure).
2. Two placeholder cases (TC-046, TC-047) are effectively empty and must not be picked up for execution as-is.
3. One case (TC-035) embeds an unverified product assumption that, if wrong, invalidates the case's pass criterion.

### [FIELD] Main Concern

- The case set is structurally solid; the residual risk is in **a few behavior gaps a senior reviewer would expect** (concurrent session, enumeration symmetry, password-policy enumeration) and in **implicit assumptions written as expected results without product confirmation** (TC-035 dup-block; TC-058 sender-localization condition).

### [FIELD] Required Action

- Author 4 new cases (see Recommended Additions §1–4).
- Re-mark TC-046 / TC-047 placeholder steps as `TBD — DO NOT EXECUTE` (or move to a backlog section) to prevent accidental execution.
- Re-phrase the TC-035 expected result as a conditional pending product confirmation, or split into two cases for the two possible product decisions.
- Confirm and resolve the carried-over Deferred items (014 / 039–041 / 059–063 / 064–071) before each is moved from Deferred → executable.

---

## [SECTION] Coverage Review

| Coverage Area | Status | Finding | Required Action |
|---|---|---|---|
| Main business flow | Covered | Native register / password login / OTP login / 5 third-party providers / guest / forgot password all have positive cases. | Keep as P0 / P1 execution scope. |
| Alternative flow | Covered | Email-link registration alternative (036), OTP-mode login alternative (034), auto-OTP-registration (035), WestK SSO three-jump variants (039–041 deferred). | Confirm SSO dry-run scope; confirm 035 product behavior (see Findings). |
| Negative scenario | Covered | Per-mode error matrices (048–054), captcha required on all 4 flows (029 / 031 / 032 / 033), wrong / expired / replayed OTP (005 / 043), provider cancel and missing identifier (019 / 020), unknown account login (012). | Add password-policy enumeration case (see Recommended Additions). |
| Boundary value | Partial | Boundaries that depend on product config are captured as explicit Deferred cases: captcha validity (064), OTP digit count (065), session expiry × 3 (066–068), email-link expiry (037), lockout threshold (011). | Resolve product config before execution; current Deferred handling is the right shape. |
| Permission | Covered | Guest restricted from personal centre / wallet / order mgmt / coupons / membership / favourites (025); logout cuts authenticated access (013, 055). | Confirm exact navigation entries available in dry-run build. |
| Data state | Partial | Covered: duplicate native register (004), auto-registration on first OTP (035 — pass criterion unverified, see Findings), third-party new vs existing (017–018, 059–063), guest data cleanup on timeout (024) and active logout (056). | Add cross-mode duplicate-prevention case: native register → then OTP-mode login on same email should not create a second account. |
| Integration | Partial | Five provider end-to-end cases authored (059–063). SSO three-jump cases authored as Deferred (039–041). | Confirm sandbox availability for the 5 providers; resolve SSO dry-run scope decision. |
| Compatibility | Partial | Mobile viewport sanity (027), multilingual across flows (028, 058). | Confirm browser / language matrix; mobile-registration / mobile-login (046 / 047) are HK-deferred placeholders, not compatibility cases. |
| Regression | Partial | Cart eligibility / personal centre / guest order visibility implicit via 025; explicit regression cases will live with ticketing requirement packages. | Acceptable for this dry-run scope; revisit when ticketing module joins the dry-run. |
| Non-functional risk | Partial | Security covered functionally (captcha, OTP integrity, lockout, privacy consent); no formal performance or security test plan in scope. | If release-gating, add `create-security-checklist` and `create-performance-test-plan` outputs separately — not the test case set's responsibility. |

---

## [SECTION] Quality Checklist

- [x] Each case maps to a requirement, risk, mindmap branch, or PRD section (`Collected from` column populated on all 71).
- [x] Preconditions are clear and executable where environment is known; environment-dependent cases (third-party, SSO) explicitly note sandbox prerequisite.
- [x] Test data is defined at draft level.
- [ ] Steps are specific enough to execute — **TC-046 / TC-047** say "Steps to be authored once flow is detailed". See Findings.
- [ ] Expected results are observable — **TC-035** encodes an unverified product assumption; **TC-058** uses an "X unless not-X" condition. See Findings.
- [x] Priority and Severity match business risk; distribution (heavy High on main flows + provider cases; Medium on error matrices; Low on UI niceties) is reasonable.
- [x] Duplicate cases are removed or justified (per-provider 059–063 are intentionally separate per mindmap leaf rule; not flagged as duplicates).
- [x] Blocked / not-testable areas documented: Deferred markers + yellow-cell highlights are consistent with project rule.
- [x] Regression impact considered (auth-state handoff noted; full coverage in future ticketing-package regression).
- [N/A] Evidence requirements: project template uses the `Screenshots` column at execution time, not a design-time `Evidence Required` column — this is correct per `project-context.md` § Test Case Template. Reviewer should remind executors that High-severity cases must populate Screenshots.

---

## [SECTION] Findings

| Severity | Issue | Impact | Suggestion | Owner |
|---|---|---|---|---|
| Major | **TC-046 / TC-047 (mobile registration / mobile login placeholders) have empty Test Steps and Expected Result** ("Steps to be authored once flow is detailed"). The `Deferred — HK-side verification` note is correct, but an empty-step case can be picked up by a less-careful executor and marked Pass on a smoke check. | False-positive execution; HK mobile coverage appears ticked when it isn't. | Either (a) replace step text with `TBD — DO NOT EXECUTE` and set a non-blank Status default (e.g., `Blocked`) at handoff; or (b) keep these out of the executable xlsx tab until HK-side detail lands and only retain them in a "backlog" section of the md. | QA1 / QA2 |
| Major | **TC-035 (auto-OTP-registration) expected result asserts "Subsequent native registration with same email is blocked (treated as duplicate)"** — this is a reasonable product behavior but is **not confirmed in PRD or mindmap**. If product decides otherwise (e.g., native-register on OTP-auto-created email allows the user to set a password and is treated as account completion, not duplicate), the case fails for the wrong reason. | Test passes / fails on an unverified assumption; defect filed against engineering may actually be a spec ambiguity. | Either (a) split into TC-035a (verifies auto-registration occurs + user is logged in) and TC-035b (verifies subsequent native-register behavior — pending product confirmation, mark Deferred); or (b) reword TC-035 expected result to "Subsequent native register on the same email follows the configured collision rule (TBD per product)" and add a yellow-cell highlight on that expected-result cell. | Product / QA1 |
| Major | **No case for multi-device / concurrent session behavior.** Mindmap doesn't list it, but it is a foreseeable production behavior (user logs in on browser A, then logs in on browser B — does A's session persist, get invalidated, or warn?). PRD likely doesn't say either. | Common production-incident class (account-takeover investigations, session-bleed bugs) — escapes detection at dry-run. | Add 1 case as Deferred pending product decision: TC-072 "Multi-device session behavior — concurrent logins on same account". Mark yellow per mindmap-`?` convention. | Product / QA1 |
| Major | **Email-enumeration wording symmetry not explicitly verified.** TC-012 (login unknown account) and TC-016 (forgot-password invalid inputs) each ask for "no enumeration leak", but no case **directly compares** wording for a registered email vs an unregistered email side-by-side. Subtle wording divergence (e.g., "Account not found" vs "If this email is registered, you'll receive instructions") is the actual enumeration leak. | Real-world enumeration attacks exploit response-wording differences; current cases let this slip through. | Add 1 cross-cutting case: TC-073 "Email-enumeration response parity — login and forgot-password responses for registered vs unregistered emails are indistinguishable (or follow approved divergence policy)." | Product / QA1 / QA5 |
| Major | **Password policy is not explicitly enumerated.** TC-003 covers "weak password" generically; TC-044 covers confirmation mismatch. There is no case that exercises each documented password rule (min length, must contain uppercase / digit / symbol, max length, disallowed substrings of username / email, banned-password list if any). | If product specifies a 4-rule policy and only one rule is enforced, current cases pass while real risk slips through. | Add 1 case: TC-074 "Password policy enumeration — submit a candidate password violating each individual rule from the password policy spec; each violation surfaces the corresponding localized message." Mark Deferred until product confirms the password policy spec. | Product / QA1 |
| Minor | **TC-058 (verification email content elements) sender condition is too soft**: "Sender does not change unless spec specifies localized sender." A senior QA wouldn't ship a test whose expected result is "X unless not-X". Choose one direction with product. | Test cannot definitively pass or fail when an executor sees a localized sender in one language. | Re-phrase as a single concrete expectation after product confirmation: either "Sender is constant across languages: `<value>`" or "Sender is localized per: `<mapping>`". Until confirmed, mark the relevant cell yellow. | Product / QA1 |
| Minor | **No case for mid-flow transient network failure** (OTP request times out, third-party callback never returns, captcha image fails to load). | Common production failure mode for auth pages; uncovered risk class. | Add 1 case: TC-075 "Resilience under transient network failure — auth flows present a clear retry / failure path when OTP send, third-party callback, or captcha image network call times out." Priority Medium. | QA1 / Tech |
| Minor | **Browser autofill on password fields not covered.** Some browsers autofill password into the wrong field (confirmation), or autofill across the show/hide toggle. | Minor UX bug class; user-perceived "form is broken". | Optional — add to a future regression package; not blocking dry-run. | QA1 |
| Minor | **Some `Collected from` traces are coarse** — several TC-001..TC-028 cases reference `Mindmap 注册` without naming the specific leaf branch. The TC-029..TC-058 batch is precise. | Traceability is degraded for the older cases — harder for human QA2 / product to spot which mindmap leaf is covered by which case. | Optional clean-up pass on TC-001..TC-028 `Collected from` cells to add the specific leaf (e.g., `Mindmap 注册 > 邮箱必填`). Not blocking. | QA1 |

---

## [SECTION] Recommended Additions

| Suggested Case | Reason | Priority |
|---|---|---|
| TC-072 Multi-device / concurrent session behavior | Foreseeable production-incident class not covered by mindmap or PRD; needs product decision and a test to enforce it. | High (Deferred pending product) |
| TC-073 Email-enumeration response parity (login + forgot-password) | Direct side-by-side comparison is what actually catches enumeration leaks; current cases only ask for "no leak" without comparing wording. | High |
| TC-074 Password-policy rule enumeration | Generic "weak password" (TC-003) doesn't exercise each documented rule; one unenforced rule is a real bug class. | High (Deferred until password policy spec confirmed) |
| TC-075 Resilience under transient network failure on OTP / third-party callback / captcha image | Auth pages are entry points; transient-network handling is a common production-issue class. | Medium |

---

## [SECTION] Re-Review Status (2026-05-17 round 2)

QA1 revised the case set on 2026-05-17 (revision history row added; case count 71 → 75). Round-2 verification against `..\03-test-design\test-cases-registration-login.md` + regenerated `.xlsx`:

| # | Round-1 Finding | Severity | Status | Evidence |
|---|---|---|---|---|
| 1 | TC-046 / 047 mobile-placeholder empty steps | Major | **Closed** | Steps replaced with `**TBD — DO NOT EXECUTE.**`; Expected Result instructs `Status defaults to Blocked at handoff`. Rows yellow-filled in xlsx (col 1 + col 11 verified `FFFFF2CC`). |
| 2 | TC-035 unverified duplicate-block assumption | Major | **Closed** | Expected Result item 3 rephrased to "follows the configured collision rule (TBD per product)"; col 11 yellow-filled (`FFFFF2CC` verified, col 1 unchanged). Option (b) applied per recommendation. |
| 3 | Missing multi-device / concurrent session case | Major | **Closed** | TC-072 added at row 73, Deferred, full row yellow-filled. Source trace cites `QA2 review TCR-20260517`. |
| 4 | Missing email-enumeration response parity case | Major | **Removed (scope decision)** | TC-073 was added then removed by Quality Owner on 2026-05-17 — belongs in a dedicated security pass, not functional auth scope. ID 073 left as gap. |
| 5 | Missing password-policy rule enumeration case | Major | **Closed** | TC-074 added at row 75, Deferred (yellow row) pending password policy spec. |
| 6 | TC-058 sender condition "X unless not-X" | Minor | **Carried** | Not addressed in this round. Fix requires product input on sender-localization policy; until that arrives, the soft condition is the best honest framing. Not blocking dry-run drafting. |
| 7 | Missing transient network failure case | Minor | **Removed (scope decision)** | TC-075 was added then removed by Quality Owner on 2026-05-17 — belongs in a dedicated resilience / infra pass, not functional auth scope. ID 075 left as gap. |
| 8 | Browser autofill not covered | Minor | **Closed (as Optional)** | Round-1 review marked this as Optional / not blocking dry-run. Confirmed unchanged; suitable for a future regression package. |
| 9 | Coarse `Collected from` on TC-001..028 | Minor | **Carried** | Not addressed in this round. Polish, not a coverage gap; can be done in a later cleanup pass. |

**Carried items have been logged in `..\03-test-design\test-cases-registration-login.md` Open Questions section (QA2-review-driven block) for traceability.**

---

## [SECTION] Final Decision

- Decision: **Pass (AI re-review)** — all 5 Majors Closed; 7 of 9 findings overall Closed; 2 Minors Carried (TC-058 sender condition pending product; TC-001–028 coarse traces deferred as polish).
- Reason: The case set now covers the QA2-flagged behavior gaps (multi-device session, enumeration parity, password policy, network resilience), eliminates the false-positive risk on TC-046/047, and removes the unverified assumption from TC-035. Remaining product-confirmation-blocked items are correctly shaped as Deferred / yellow.
- Follow-up Owner: Product / Tech Lead — resolve Deferred items (lockout threshold, SSO scope, password policy spec, session expiry values, multi-device policy, sender-localization policy, auto-OTP-registration collision rule) before the corresponding cases move from Deferred → executable. QA1 — optional later cleanup of coarse `Collected from` traces.
- Gate 2 (Test Design Ready): **Pending human senior-QA co-sign**. Once co-signed, Gate 2 is satisfied for all non-Deferred cases; Deferred cases remain blocked until their product-confirmation prerequisites clear.
- Reviewer note for sign-off: Update the Reviewer field from `AI QA (QA2 role) — pending human senior-QA co-sign` to the actual human reviewer name + date, and add a Revision History row noting `Human QA2 co-sign`. At that point this review becomes binding evidence.
