# Test Case Review

---

## [SECTION] Review Summary

- Review target: `..\test-cases-registration-login.md` v1 (73 cases) — Round 1 of iterate-test-case-quality loop
- Requirement / feature: West Kowloon Website registration and login (2026-05 dry-run)
- Overall result: **Needs Revision**
- Main concern: Two cases (TC-051..054 and TC-070) carry obsolete framing that was true at draft time but is now contradicted by execution evidence already recorded in the file itself. Leaving them as-is means the next executor either repeats a known-invalid attempt or skips a now-answerable check.

---

## [SECTION] Coverage Review

| Coverage Area | Status | Finding | Required Action |
|---|---|---|---|
| Main flow | Covered | Native register / password login / OTP login / 5 providers / guest / forgot password all have positive cases (TC-001, 009, 015, 017, 021, 034 etc.). | None. |
| Negative scenario | Covered | Per-mode error matrices, captcha required on all 4 flows, wrong/expired/replayed OTP, provider cancel/missing identifier. | None. |
| Boundary value | Partial | Captcha validity, OTP digit count, session expiries, lockout threshold all captured as explicit Deferred (064–068). Shape is correct. | None blocking. |
| Permission | Covered | Guest restrictions (025), logout cuts auth access (013, 055). | None. |
| Data state | Partial | Duplicate native register (004 — caught a real defect), auto-OTP-registration (035), third-party new/existing (017–018, 059–063), guest cleanup (024, 056). | One residual finding (see Finding 3). |
| Integration | Partial | Five provider end-to-end (059–063) + SSO three-jump (039–041) as Deferred. | Sandbox / SSO scope decisions are Deferred — correctly shaped. |
| Compatibility | Covered | Mobile viewport (027), multilingual (028, 058). | None. |
| Regression | Partial | Cart eligibility / personal centre implicit via 025; explicit regression to ticketing-package. | Acceptable for dry-run scope. |
| Non-functional risk | Partial | Security covered functionally (captcha, OTP integrity, lockout, privacy); no separate perf / sec plan. | Out of scope per Quality Owner decision (TC-073, 075 removed). |

---

## [SECTION] Findings

| Severity | Issue | Impact | Suggested Fix |
|---|---|---|---|
| Major | **TC-051..054 (OTP-mode multi-field-wrong matrices) carry an obsolete 4-field design**. The case bodies say "email + password + 动态码 + 验证码" but the in-file Actual Result on all four is "OTP-mode login on SIT uses three fields (email / 动态码 / 验证码) with no password field, so the … matrix in the test design cannot be executed faithfully". They are marked `NA` permanently. From a senior-QA perspective: a case that documents its own design as incompatible with implementation should either be **rewritten** for the 3-field reality OR **formally retired** with IDs left as gaps (the same treatment TC-073/075 received). Leaving them as eternal NA pollutes coverage stats and invites the next executor to retry a known-invalid combination. | Coverage statistics inflated; executor confusion; review fatigue. | Choose one: (a) retire TC-051..054, leave IDs as gaps, document in Revision History per the TC-073/075 precedent; OR (b) rewrite as TC-051a/b/c covering the actual 3-field matrix (1-wrong / 2-wrong / all-wrong over email / 动态码 / 验证码). Per [[project_west_kowloon_source_authority]] mindmap is authoritative for scope — but mindmap describes a 4-field design that the build does not implement, which itself is an Open Question that belongs in 02-analysis. |
| Major | **TC-070 (forgot-password reset model) is stale Deferred**. The case is marked `Deferred — model TBD`, but the in-file Actual Result already records the answer: "As expected - direct-reset model. UI-confirmed 2026-05-23: forgot-password page exposes Email tab + Reset with phone + Get Code + Continue buttons; flow is email → OTP → set new password. No temp-password emailing." The model question is **answered**, yet the case remains Deferred with `Status = NA`. The system has no mechanism to promote a Deferred case once its prerequisite resolves. | A resolved Open Question stays masked as "unknown" in the test design; downstream coverage reports under-count the now-testable case; QA process loses the audit trail for "when was this Deferred case actually answered". | Promote TC-070 from Deferred to executable. Split into TC-070a "Forgot password with direct-reset OTP model succeeds end-to-end (email + 动态码 + OTP + new password sets the new password; old password no longer authenticates)" — testable now. Retain a brief TC-070b note "No temp-password is ever emailed by this flow" as a negative observation. Add a Revision History row documenting the promotion + cite the 2026-05-23 SIT confirmation as source. |
| Minor | **TC-026 (duplicate submit / loading state) only covers login + register**. Forgot-password (TC-015) and guest robot-verification (TC-022) are the other flows with submit-buttons that can be double-clicked; same bug class (double-OTP-request, double-captcha-submit) applies. The mindmap doesn't call this out explicitly, but it is a foreseeable production-incident class — same risk profile as TC-072 multi-device. | Real production-incident class not covered for 2/4 auth flows. | Extend TC-026 scope to "all 4 auth flows" OR add TC-026a (forgot-password duplicate submit), TC-026b (guest robot-verification duplicate submit). Priority Medium. |
| Minor | **Same-account same-browser multiple-tabs not covered**. TC-072 covers concurrent sessions on different browsers/devices; not the more common case of one user opening 5 tabs of the same site (e.g., during browsing). Per-tab cookie/session sync is a known bug class for SPA sites — independent state, race on logout, identity leak between tabs. | Common real-world UX path not covered; class is independent of TC-072's cross-browser scenario. | Add TC-076 "Multi-tab same-browser session sync — login on tab 1, open tab 2: tab 2 reflects logged-in state without re-auth; logout on tab 1 invalidates tab 2 on next action." Priority Medium. Not deferred — testable today. |

---

## [SECTION] Recommended Additions

| Suggested Case | Reason | Priority |
|---|---|---|
| TC-070a (executable replacement for Deferred TC-070) | Reset model is now known per SIT evidence; case should test the now-confirmed direct-reset OTP flow end-to-end. | High |
| TC-026a / 026b OR extended TC-026 | Duplicate-submit class applies to all 4 auth flows, not just 2. | Medium |
| TC-076 multi-tab same-browser session sync | Real production UX path, independent of TC-072 cross-browser class. | Medium |
| (TC-051..054 retirement) | Documenting the retirement in Revision History per TC-073/075 precedent. | (Bookkeeping) |

---

## [SECTION] Final Decision

- Decision: **Needs Revision**
- Required changes:
  1. TC-051..054: retire (preferred — cleaner) OR rewrite for the 3-field SIT reality. Document choice in Revision History.
  2. TC-070: promote from Deferred to TC-070a executable, citing 2026-05-23 SIT confirmation. Add a Deferred Resolution row noting the source of the answer.
  3. TC-026: extend to all 4 auth flows OR add TC-026a / 026b.
  4. TC-076: add as new executable High-priority case.
- Reviewer notes: The case set is otherwise mature and reflects two genuine human-QA review rounds. The two Major findings are not v1 quality regressions — they are stale-state issues created by Deferred items getting resolved (TC-070) or by implementation diverging from mindmap (TC-051..054) without a corresponding test-design refresh. A senior reviewer would expect the design to follow the build's evolving state, not snapshot at v1 forever. Surfacing these as findings is the orchestrator's added value over the prior 2-layer chain — automated re-review catches drift the human cycle missed.
