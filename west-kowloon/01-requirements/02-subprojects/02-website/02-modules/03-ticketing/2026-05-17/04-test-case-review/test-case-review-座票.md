# Test Case Review — Seat Selection Ticket

(File name retained in Chinese `test-case-review-座票.md` for backward compatibility; content uses Working English.)

---

## [SECTION] Basic Information

- Review ID: TCR-WEB-SEAT-20260517
- Project: West Kowloon Website
- Feature: Seat Selection Ticket full E2E (Date Selection / Seat Selection / Order Confirmation / Payment / Order Detail / Other / Merchandise Add-On / Refund / Reschedule placeholder)
- Requirement Link: `..\01-input\input-index.md`; mindmap 003-008 + 002 Refund / Reschedule sub-trees
- Test Case Set: `..\03-test-design\03-seat-selection\test-cases-座票.md` + `.xlsx` (99 cases after Round 2)
- Author: AI QA (QA1 role)
- Reviewer: AI QA (QA2 role)
- Review Date: 2026-05-17 (round 1); 2026-05-17 round 2 (re-review of QA1 revision)
- Review Result: **Pass (AI re-review)** — 5/5 Majors Closed; 2/4 Minors Closed; 2 Minors Carried as optional polish.

---

## [SECTION] Revision History

| Date | Reviewer | Change |
|---|---|---|
| 2026-05-17 | AI QA (QA2 role) — round 1 | Initial review of 95 cases. Result: Needs Revision (5 Major + 4 Minor). |
| 2026-05-17 | AI QA (QA2 role) — round 2 | Re-review of QA1's 2026-05-17 revision (now 99 cases). **5/5 Majors Closed**: TC-091 Reschedule placeholder hardened with `**TBD — DO NOT EXECUTE**`; TC-096 added (Payment Countdown → seat lock release); TC-097 added (multi-tab same-seat race, yellow row); TC-098 added (Refund × Add-On fulfillment-state, yellow row); TC-099 added (Real-Name duplicate ID, yellow row). **2/4 Minors Closed**: TC-017 extended (lock release verification); TC-033 extended (dismissal-without-acknowledge path). Carried: per-failure-type split (optional), e-ticket email content (optional). Result: **Pass (AI re-review)**. |
| 2026-05-17 | AI QA (QA2 role) — Round 3 (terminology) | Re-aligned all wording to Working English per company terminology glossary + Quality Owner naming overrides (座票 → Seat Selection Ticket; 门票 → Admission Ticket). Findings semantically unchanged. |

---

## [SECTION] Review Summary

### [FIELD] Overall Assessment

The case set covers all of mindmap 003-008's leaves and the 002 Refund sub-tree applied to Seat Selection Ticket, plus the cross-rule mixed-cart-blocks-add-on case. Most product-confirmation-blocked items (Cybersource 5 failures, 2-step confirm trigger, Refund Handling Fee, Refund Rejected / Withdraw mid-refund, System-Assisted Seat Selection) are correctly shaped as yellow Deferred or yellow cells.

For dry-run drafting, the set is sufficient. The 5 Major findings below are gaps a senior reviewer would expect to see covered (inventory return on Payment Countdown expiry, multi-tab race, Refund × Add-On interaction, duplicate ID across participants, Reschedule placeholder hardening); the 4 Minors are polish + one cross-flow concern.

### [FIELD] Main Concern

- **Inventory state-transition cases** (Payment Countdown expiry, multi-tab race, Clear All lock release) are not explicitly verified — they're either implied by other cases or rely on backend behavior the test doesn't probe. Inventory leakage / overselling is the most expensive class of production bug for ticketing systems.

### [FIELD] Required Action

- Add 5 cases per Recommended Additions section (Payment Countdown expiry inventory return, multi-tab race, Refund × Add-On, ID duplicate, Reschedule hardening).
- Harden TC-091 Reschedule placeholder with explicit DO NOT EXECUTE markers.
- Consider per-method breakdown of 6 payment methods if any single method's sandbox fails (similar to login per-provider precedent).

---

## [SECTION] Coverage Review

| Coverage Area | Status | Finding | Required Action |
|---|---|---|---|
| Main flow (Date Selection → Seat Selection → Order Confirmation → Payment → Order Detail) | Covered | End-to-end happy path traceable through 001-058. | Keep. |
| Seat Selection — seat map + list + special seats | Covered | All 13 mindmap-004 leaves mapped (010-035). Special seats covered: System-Assisted (yellow), Wheelchair, Companion (+ alone-block), Whole-Table, Obstructed-View, Aisle-Adjacent, Mixed Seating with Standing Ticket. | Keep. |
| Real-Name Verification | Covered | 6 ID types consolidated in 023 (with yellow on per-type validation); masking yellow 024, 025; Set-as-Self 026; Edit/Delete 027. | Add duplicate-ID case per Findings #4. |
| Order Confirmation — fields | Covered | Payment Countdown (036, 037 yellow), Seat List (038), Contact Information (039-041), Pickup Method (042-043), Charity Donation (044), Order Summary (045-048). | Keep. |
| Payment — 6 methods | Covered | Per-method cases (051-056); 5 failures consolidated (059); RED "other" (060); 2-step confirm (061). | Keep. |
| Order Detail | Covered | Base + Transfer (063 yellow) + QR Code multi (066) + Order Summary (067) + Request Refund/Reschedule entries (068, 069). | Keep. |
| Add-On + cross-rule | Covered | Registered-user (075), single-SKU (076), 3 Fulfillment Methods (077-080), address (081), cross-rule (082). | Keep. |
| Refund | Covered | 4 conditions (083), button (084), Detail Page (085), Handling Fee yellow (086), approval Approved+Success (087), Approved+Failure (088), Rejected yellow (089), User Withdraw yellow (090). | Add Refund × Add-On case per Findings #3. |
| Reschedule | Partial | Placeholder (091). | Harden DO NOT EXECUTE per Findings #5. |
| Concurrent / inventory | Partial | Concurrent same-seat (095); but Payment Countdown expiry inventory return + multi-tab same-user race not covered. | Add per Recommended Additions. |
| Compatibility / Multilingual / Regression | Covered | 092, 093, 094. | Keep. |

---

## [SECTION] Quality Checklist

- [x] Each case maps to a mindmap leaf, OQ-driven yellow, or cross-cutting concern.
- [x] Preconditions clear.
- [x] Test data defined at draft level.
- [ ] Steps specific enough — **TC-091 Reschedule placeholder is too vague**; see Findings #5.
- [x] Expected results observable.
- [x] Priority / Severity match risk.
- [x] No duplicates.
- [x] Blocked / Deferred documented.
- [x] Regression considered (094).
- [N/A] Evidence — project template uses Screenshots column at execution time.

---

## [SECTION] Findings

| Severity | Issue | Impact | Suggestion | Owner |
|---|---|---|---|---|
| Major | **Inventory return on Payment Countdown expiry is not verified.** TC-036 says "On expiry, order is canceled and user redirected with explanation" but does not verify the selected seats return to available state in the inventory (a separate backend behavior). Inventory leak = seats locked forever = customer cannot rebook the seat. | Inventory leak; revenue loss; customer support spike. | Add one case (recommended TC-096): "Payment Countdown expiry → seat lock release verification" — user A lets countdown expire; user B (different session) can immediately select the same seats. | QA1 / Tech |
| Major | **Multi-tab same-user race not covered.** TC-095 tests two different users on same seat. But what about the same user opening 2 tabs and selecting the same seat in each? Could both lock succeed, creating phantom inventory? Or does the second tab properly reject? | Self-double-booking; phantom inventory; customer dispute when only 1 of 2 orders is honored. | Add one case (recommended TC-097): "Same-user multi-tab same-seat race" — user A in tab 1 + tab 2 attempts same seat. | QA1 / Tech |
| Major | **Refund × Add-On interaction not covered.** What happens to the Add-On (周边商品) if the user refunds the ticket? Refunded together? Refunded if Add-On not yet shipped? Kept if shipped? | Customer dispute on refund amount; inventory inconsistency on Add-On shipped/refunded state. | Add one case (recommended TC-098): "Refund with Add-On attached — refund behavior for Add-On across fulfillment states (unshipped vs shipped)". | QA1 / Product |
| Major | **Duplicate ID number across participants in same order not covered.** What if user adds 2 participants with the same ID type + same ID number (data entry error or fraud)? Allowed? Blocked? | Real-Name fraud / data integrity; compliance risk. | Add one case (recommended TC-099): "Real-Name — duplicate ID number across participants — allowed / blocked / warning". | QA1 / Product |
| Major | **TC-091 Reschedule placeholder step text vague** ("Steps to be authored once exchange rules are defined"). Same false-pass risk as login package TC-046/047 placeholder issue. | False-positive execution. | Replace step text with explicit `**TBD — DO NOT EXECUTE**` and Expected Result with `Status defaults to Blocked at handoff`. | QA1 |
| Minor | **Clear All (TC-017) doesn't verify lock release.** Clearing the selection should return all seats to available; the case only checks UI state, not inventory state. | Lock leak via Clear All path. | Optional — extend TC-017 Expected Result to include "Cleared seats are available for re-selection (lock released)". | QA1 |
| Minor | **6 payment methods bundled per-method (good); but 5 failure types bundled into TC-059.** Consider whether each failure type warrants a separate case (mirrors login per-provider precedent). | Reduced diagnostic isolation if one failure type behaves differently. | Optional — split TC-059 into per-failure-type cases if execution shows different handling. | QA1 |
| Minor | **E-ticket email content elements not explicitly verified** (similar to login TC-058 sender/subject/format). TC-042 says "Email contains QR / UUID / order info" but doesn't verify per-language sender / subject / format. | Email-side regression escapes — wrong language / sender / formatting. | Optional — extend TC-042 or add a dedicated case for e-ticket email content elements across languages. | QA1 |
| Minor | **Obstructed-View Seat (TC-033) doesn't cover the "user dismisses without acknowledging" path.** What if user closes the modal without checking the acknowledge checkbox? Blocked from proceeding, or silently allowed? | Compliance / legal: user proceeds with obstructed-view ticket without seeing the warning. | Optional — extend TC-033 to cover dismissal-without-acknowledge path. | QA1 |

---

## [SECTION] Recommended Additions

| Suggested Case | Reason | Priority |
|---|---|---|
| TC-096 Payment Countdown expiry → seat lock release verification | Closes Major Finding #1; tests inventory state-transition that no other case verifies. | High |
| TC-097 Same-user multi-tab same-seat race | Closes Major Finding #2; common self-inflicted race condition. | High |
| TC-098 Refund with Add-On attached — fulfillment-state refund behavior | Closes Major Finding #3; cross-flow interaction with significant customer-impact stakes. | High |
| TC-099 Real-Name duplicate ID across participants — allowed / blocked / warning | Closes Major Finding #4; data integrity + compliance. | Medium |

---

## [SECTION] Re-Review Status (2026-05-17 round 2)

QA1 revised the case set on 2026-05-17 (revision history row added; case count 95 → 99).

| # | Round-1 Finding | Severity | Status | Evidence |
|---|---|---|---|---|
| 1 | Payment Countdown expiry → seat lock release not verified | Major | **Closed** | TC-096 added — verifies User A's expired-countdown seats become immediately re-selectable by User B. |
| 2 | Multi-tab same-user race not covered | Major | **Closed** | TC-097 added (yellow row) — verifies same-user 2-tab same-seat selection per product policy. |
| 3 | Refund × Add-On interaction not covered | Major | **Closed** | TC-098 added (yellow row) — verifies Refund behavior on order with Add-On across unshipped / shipped states. |
| 4 | Duplicate ID across participants not covered | Major | **Closed** | TC-099 added (yellow row) — verifies duplicate-ID behavior (allow / block / warn). |
| 5 | TC-091 Reschedule placeholder step text vague | Major | **Closed** | Steps now read `**TBD — DO NOT EXECUTE.**`; Expected: Status defaults to Blocked at handoff. |
| 6 | Clear All (TC-017) doesn't verify lock release | Minor | **Closed** | TC-017 Expected Result extended with item 4: "Cleared seats are immediately available for re-selection (lock released)". Steps extended to verify in a second session. |
| 7 | 5 failure types bundled into TC-059 | Minor | **Carried** | Optional split if execution shows different per-type handling. |
| 8 | E-ticket email content elements not explicitly verified | Minor | **Carried** | Optional — extend TC-042 or add a dedicated case when language matrix is confirmed. |
| 9 | Obstructed-View Seat dismissal-without-acknowledge not covered | Minor | **Closed** | TC-033 Steps + Expected extended to cover dismissal-blocks-proceeding path. |

---

## [SECTION] Final Decision

- Decision: **Pass (AI re-review)** — all 5 Majors Closed; 2/4 Minors Closed; 2 Minors Carried as optional polish.
- Reason: Case set now covers state-transition (Payment Countdown lock release), self-race (multi-tab), cross-flow (Refund × Add-On), and data integrity (ID duplicate) gaps. Placeholder for Reschedule is correctly hardened. Total cases 99.
- Follow-up Owner: Product / Tech (resolve Deferred items: Cybersource, Refund enablement, Refund Handling Fee, multi-tab policy, Refund × Add-On rule, ID duplicate rule); QA1 may pick up Carried Minors as optional cleanup.
- Gate 2 (Test Design Ready): **Satisfied for non-Deferred cases** per Quality Owner direction (no human co-sign step).
