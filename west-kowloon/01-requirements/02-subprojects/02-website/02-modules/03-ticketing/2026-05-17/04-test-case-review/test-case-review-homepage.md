# Test Case Review — Homepage

---

## [SECTION] Basic Information

- Review ID: TCR-WEB-HOME-20260517
- Project: West Kowloon Website
- Feature: Homepage (event detail page + Buy Tickets entry routing + figma-only Combo Ticket / Cross-Session Bundle Ticket placeholders)
- Requirement Link: `..\01-input\input-index.md`; mindmap 001, 002 top-level; figma main flow + Combo Ticket + Cross-Session Bundle Ticket
- Test Case Set: `..\03-test-design\01-homepage\test-cases-homepage.md` + `.xlsx` (33 cases after Round 2)
- Author: AI QA (QA1 role)
- Reviewer: AI QA (QA2 role)
- Review Date: 2026-05-17 (round 1); 2026-05-17 round 2 (re-review of QA1 revision)
- Review Result: **Pass (AI re-review)** — 4/4 Majors Closed; 1/4 Minors Closed; 3 Minors Carried as optional polish / out-of-scope.

---

## [SECTION] Revision History

| Date | Reviewer | Change |
|---|---|---|
| 2026-05-17 | AI QA (QA2 role) — round 1 | Initial review of 30 cases. Result: Needs Revision (4 Major + 4 Minor). |
| 2026-05-17 | AI QA (QA2 role) — round 2 | Re-review of QA1's 2026-05-17 revision (now 33 cases). **4/4 Majors Closed**: TC-021/022 placeholder Steps hardened with `**TBD — DO NOT EXECUTE**`; TC-031 added (Wishlist intent across login, yellow cell); TC-032 added (Recommended Events + Same-Venue empty-state); TC-033 added (single-variant Buy Tickets entry routing). **1/4 Minors Closed**: none directly addressed; Carried: TC-004 Share platform split (optional), View Discounts expired (optional), stale-data (optional). Accessibility out of scope per Kasi functional scope discipline. Result: **Pass (AI re-review)**. |
| 2026-05-17 | AI QA (QA2 role) — Round 3 (terminology) | Re-aligned all wording to Working English per company terminology glossary + Quality Owner naming overrides (座票 → Seat Selection Ticket; 门票 → Admission Ticket). Findings semantically unchanged. |

---

## [SECTION] Review Summary

### [FIELD] Overall Assessment

The case set covers every leaf on mindmap 001 and the 002 top-level Buy Tickets entry, plus the two figma-only placeholders (Combo Ticket / Cross-Session Bundle Ticket). Coverage is mostly complete for a homepage scope; remaining gaps are around edge-state behavior (empty-result Recommended Events, Wishlist state transitions across login boundaries) and the placeholder cases need the same "DO NOT EXECUTE" hardening that the login package adopted for TC-046/047.

For dry-run drafting, the set is sufficient. For execution, the 4 Major items below should be addressed first.

### [FIELD] Main Concern

- **Wishlist behavior across login state transitions** (guest add → login → state?) is not covered, and TC-003 / TC-026 are too vague — they ask "behavior TBD" without authoring the two possible cases for the two possible product decisions.

### [FIELD] Required Action

- Harden TC-021 / TC-022 placeholder cases with explicit `**TBD — DO NOT EXECUTE**` step markers (per login package convention).
- Add empty-state cases for Recommended Events (TC-020) and Same-Venue Related Events (TC-018) — what if the API returns 0 items?
- Add Wishlist state-transition case: guest tries to add → prompted to login → after login, was the intent preserved?
- Consider per-platform separation for Share (TC-004) IF QA experience shows different platforms fail independently in SIT.

---

## [SECTION] Coverage Review

| Coverage Area | Status | Finding | Required Action |
|---|---|---|---|
| Main page elements | Covered | All 13 mindmap 001 nodes mapped to cases. | Keep. |
| Figma-only items | Covered | Combo Ticket (021), Cross-Session Bundle Ticket (022) — yellow placeholder rows. | Harden Steps per Findings #1. |
| Mindmap-`?` items | Covered | Each ? has a yellow cell or yellow row (008, 010, 011, 012, 017, 020 + 003/026 for guest behavior). | Keep. |
| Negative scenario | Partial | 404 (028), back-nav (027), loading (030) covered. Empty-result for Recommended Events not covered. | Add per Recommended Additions. |
| Permission | Covered | Guest behavior on Wishlist (003, 026) + login regression (025). | Re-author 003/026 as concrete cases per Findings #3. |
| Compatibility | Covered | Mobile viewport (023). | Keep. |
| Multilingual | Covered | One cross-cutting case (024). | Keep. |
| Regression | Covered | Login → homepage → Buy Tickets entry (025). | Keep. |
| Non-functional risk | Partial | Loading state (030); no perf / sec test plan in scope. | Acceptable for dry-run. |

---

## [SECTION] Quality Checklist

- [x] Each case maps to a mindmap node, figma node, or cross-cutting concern.
- [x] Preconditions clear and executable.
- [x] Test data defined.
- [ ] Steps specific enough to execute — **TC-021 / TC-022 placeholders are too vague**; see Findings #1.
- [ ] Expected results observable — **TC-003 / TC-026 use "TBD per product" without authoring the alternatives**; see Findings #3.
- [x] Priority and Severity match risk.
- [x] No accidental duplicates.
- [x] Blocked / Deferred areas documented (placeholders + yellow rows).
- [x] Regression considered (025).
- [N/A] Evidence — project template uses Screenshots column at execution time.

---

## [SECTION] Findings

| Severity | Issue | Impact | Suggestion | Owner |
|---|---|---|---|---|
| Major | **TC-021 (Combo Ticket) and TC-022 (Cross-Session Bundle Ticket) placeholder cases have vague step text** ("Steps to be authored once mindmap captures..."). A less-careful executor can pick these up and false-pass on a smoke check (same risk that bit login package TC-046/047 in v1). | False-positive execution; placeholder coverage looks ticked when nothing was tested. | Replace step text with explicit `**TBD — DO NOT EXECUTE**` and set Expected Result to instruct `Status defaults to Blocked at handoff`. Mirror login package's QA1 revision pattern. | QA1 |
| Major | **Wishlist behavior across login state transitions not covered.** TC-003 covers "guest clicks Add to Wishlist — login prompt or block?" with Expected Result "TBD per product". TC-026 same. There is no case for the actual transition: guest adds → prompted to login → after login, is the wishlist intent preserved (auto-added) or lost (user must click again)? | Real-world UX failure mode — silent intent loss after login feels broken to users. | Add one case (recommended TC-031): "Wishlist intent preservation across login transition" — verify a guest's wishlist-add intent survives the login redirect and the event is added after authentication. | QA1 / Product |
| Major | **Empty-state behavior for Recommended Events (TC-020) and Same-Venue Related Events (TC-018) not covered.** What if the recommendation engine returns 0 events, or the venue has only this one event? Current cases assume content exists. | Empty result may render badly (broken layout, "undefined" placeholder, or section disappears entirely) — common production bug class. | Add one case (recommended TC-032): "Recommendation + same-venue sections — empty-state behavior" — verify both sections render gracefully when data is empty (hidden section vs explicit "no recommendations" message). | QA1 / Product |
| Major | **TC-013 / TC-016 split — Buy Tickets entry routing assumes event has BOTH ticket types.** What if event has only Seat Selection Ticket, or only Admission Ticket? Current cases don't cover the single-variant routing. | Single-variant events may surface a "pick variant" UI that's broken or hides the entry button. | Add one case (recommended TC-033): "Buy Tickets entry — single-variant event (Seat-Selection-only OR Admission-only)" — verify entry skips variant selection and routes directly to Date Selection. | QA1 |
| Minor | **TC-004 (Share) bundles 9 platforms** into one case. If any platform fails (e.g., WeChat sandbox unavailable in SIT, LinkedIn / Xiaohongshu sub-platform integration not ready), executor will mark the whole case Fail without isolating which platform failed. | Reduced diagnostic value; harder to triage. | Optional — split into per-platform sub-cases (mirrors login package per-provider TC-059..063 pattern). Or keep bundled with an explicit per-platform sub-result table inside the case. | QA1 |
| Minor | **View Discounts expiration / inactive state not covered.** TC-006 verifies active discount display; no case for an expired or inactive discount. | Expired discounts might still show as applicable, leading to checkout errors. | Optional — add a case for "View Discounts — expired / inactive discount visibility" | QA1 |
| Minor | **Accessibility not covered** — keyboard navigation, screen reader labels (e.g., aria-label on Wishlist toggle, focus order through Share menu). | Accessibility regression risk for entry-point page; legal concern in some regions. | Out of scope per Quality Owner direction (functional scope discipline). Note for a dedicated accessibility pass. | — |
| Minor | **Stale-data state not covered** — what if event details (price / availability / image) change while user is viewing the homepage? | Stale display can mislead users into starting a purchase under wrong context. | Optional — add a case "Stale event data while homepage open — refresh / mismatch behavior". | QA1 |

---

## [SECTION] Recommended Additions

| Suggested Case | Reason | Priority |
|---|---|---|
| TC-031 Wishlist intent preservation across login transition | Closes Major Finding #2; tests real UX flow that's not in any other case. | High |
| TC-032 Recommendation + same-venue empty-state behavior | Closes Major Finding #3; covers a common production bug class. | Medium |
| TC-033 Buy Tickets entry — single-variant event (Seat-Selection-only OR Admission-only) | Closes Major Finding #4; current cases assume both variants. | High |

---

## [SECTION] Re-Review Status (2026-05-17 round 2)

QA1 revised the case set on 2026-05-17 (revision history row added; case count 30 → 33).

| # | Round-1 Finding | Severity | Status | Evidence |
|---|---|---|---|---|
| 1 | TC-021 / 022 placeholder Steps too vague | Major | **Closed** | Steps now read `**TBD — DO NOT EXECUTE.** Steps will be authored once...`; Expected: `**DO NOT EXECUTE** ... Status defaults to Blocked at handoff`. Yellow rows verified. |
| 2 | Wishlist behavior across login state transitions not covered | Major | **Closed** | TC-031 added — verifies guest-add → login → intent preservation (or not, per product). Yellow cell on Expected Result col 11 (product policy TBD). |
| 3 | Empty-state behavior for Recommended Events / Same-Venue Related Events not covered | Major | **Closed** | TC-032 added — verifies graceful empty-state rendering for both sections. |
| 4 | Buy Tickets entry single-variant routing not covered | Major | **Closed** | TC-033 added — verifies Seat-Selection-only and Admission-only events route directly to Date Selection without empty variant picker. |
| 5 | TC-004 Share bundles 9 platforms | Minor | **Carried** | Optional split per Round 1 finding; not blocking dry-run drafting. |
| 6 | View Discounts expiration / inactive state not covered | Minor | **Carried** | Optional add; not blocking dry-run drafting. |
| 7 | Accessibility not covered | Minor | **Removed (scope)** | Out of scope per Quality Owner functional scope discipline (memory: dedicated accessibility pass). |
| 8 | Stale-data state not covered | Minor | **Carried** | Optional add; not blocking dry-run drafting. |

---

## [SECTION] Final Decision

- Decision: **Pass (AI re-review)** — all 4 Majors Closed; Carried Minors are optional polish.
- Reason: Case set now covers the QA2-flagged behavior gaps (Wishlist transition, empty-state, single-variant routing) and the 2 placeholders are correctly hardened. Total cases 33.
- Follow-up Owner: Product / Tech (resolve Deferred Open Questions when ready); QA1 may pick up Carried Minors as optional cleanup.
- Gate 2 (Test Design Ready): **Satisfied for non-Deferred cases** per Quality Owner direction (no human co-sign step). Deferred cases remain blocked until product prerequisites clear.
