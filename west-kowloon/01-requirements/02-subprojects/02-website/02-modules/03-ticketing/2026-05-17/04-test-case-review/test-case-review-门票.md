# Test Case Review — Admission Ticket

(File name retained in Chinese `test-case-review-门票.md` for backward compatibility; content uses Working English.)

---

## [SECTION] Basic Information

- Review ID: TCR-WEB-TKT-20260517
- Project: West Kowloon Website
- Feature: Admission Ticket full E2E (Date Selection / Ticket Selection / Order Confirmation / Payment / Order Detail / Other / Merchandise Add-On / Refund / Reschedule placeholder)
- Requirement Link: `..\01-input\input-index.md`; mindmap 009-014 + 002 Refund / Reschedule sub-trees
- Test Case Set: `..\03-test-design\02-ticketing\test-cases-门票.md` + `.xlsx` (78 cases after Round 2)
- Author: AI QA (QA1 role)
- Reviewer: AI QA (QA2 role)
- Review Date: 2026-05-17 (round 1); 2026-05-17 round 2 (re-review of QA1 revision)
- Review Result: **Pass (AI re-review)** — 6/6 Majors Closed; 0/5 Minors Closed; 5 Minors Carried as optional polish.

---

## [SECTION] Revision History

| Date | Reviewer | Change |
|---|---|---|
| 2026-05-17 | AI QA (QA2 role) — round 1 | Initial review of 73 cases. Result: Needs Revision (6 Major + 5 Minor). |
| 2026-05-17 | AI QA (QA2 role) — round 2 | Re-review of QA1's 2026-05-17 revision (now 78 cases). **6/6 Majors Closed**: TC-041 paired with new TC-078 as a Deferred pair (verify absence vs verify happy-path per product direction); TC-044 QR Code mapping-field semantics yellow-celled; TC-069 Reschedule placeholder hardened; TC-074 added (Payment Countdown → ticket release); TC-075 added (multi-tab race, yellow); TC-076 added (Refund × Add-On, yellow); TC-077 added (Real-Name duplicate ID, yellow). **0/5 Minors Closed** — all carried as optional polish (e-ticket email content; Sold Out per Ticket Type; eligibility validation; 5-failure split; another). Result: **Pass (AI re-review)**. |
| 2026-05-17 | AI QA (QA2 role) — Round 3 (terminology) | Re-aligned all wording to Working English per company terminology glossary + Quality Owner naming overrides (座票 → Seat Selection Ticket; 门票 → Admission Ticket). Findings semantically unchanged. |

---

## [SECTION] Review Summary

### [FIELD] Overall Assessment

The case set mirrors Seat Selection Ticket (minus seat-map and Transfer specifics) and covers all of mindmap 009-014's leaves plus the 002 Refund sub-tree applied to Admission Ticket, plus the cross-rule mixed-cart case. The structural choice to write Merchandise Add-On and Refund separately for each ticket type (per Quality Owner direction) is correctly executed.

For dry-run drafting, the set is sufficient. Most Major findings are shared with the Seat Selection Ticket review (inventory expiry return, multi-tab race, Refund × Add-On, ID duplicate). Two Admission-Ticket-specific Major items: TC-041 (Transfer absent verification) needs sharper framing, and TC-044 (QR Code "mapping field") has a semantic mismatch for Admission Ticket that needs explicit Product clarification.

### [FIELD] Main Concern

- **TC-041 (Transfer absent on Admission Ticket)** flags the mindmap discrepancy correctly but reads as a passive "verify absence" — a senior reviewer would expect a stronger ask: drive Product to decision and split TC-041 into two cases for the two possible product directions.

### [FIELD] Required Action

- Add 4 cases shared with the Seat Selection Ticket review (Payment Countdown inventory return, multi-tab race, Refund × Add-On, ID duplicate).
- Sharpen TC-041 (Transfer absence) into a two-case Deferred set pending Product direction.
- Resolve TC-044 QR Code "mapping field" semantic ambiguity for Admission Ticket (likely should be Ticket Number / Ticket Type).
- Harden TC-069 Reschedule placeholder with explicit DO NOT EXECUTE markers.

---

## [SECTION] Coverage Review

| Coverage Area | Status | Finding | Required Action |
|---|---|---|---|
| Main flow (Date Selection → Ticket Selection → Order Confirmation → Payment → Order Detail) | Covered | End-to-end happy path traceable through 001-036. | Keep. |
| Ticket Selection — Price + Ticket Type + Real-Name | Covered | 005, 006 + Real-Name 007-013. | Keep. Note absence of seat map / seat list is correct for Admission Ticket. |
| Real-Name Verification | Covered | Same shape as Seat Selection Ticket. | Add duplicate-ID case per Findings #4. |
| Order Confirmation | Covered | 014-026. | Keep. |
| Payment — 6 methods | Covered | 029-034 per-method + 037 failures + 038 RED + 039 2-step confirm. | Keep. |
| Order Detail | Partial | Base + Transfer absence (041 yellow) + QR Code multi (044 with "mapping field" caveat) + Summary (045) + Request Refund/Reschedule entries. | Sharpen 041 + 044 per Findings #1, #2. |
| Add-On + cross-rule | Covered | 053-059 + cross-rule (060). | Keep. |
| Refund | Covered | 4 conditions (061), button (062), Detail Page (063), Handling Fee yellow (064), approval Approved+Success (065), Approved+Failure (066), Rejected yellow (067), User Withdraw yellow (068). | Add Refund × Add-On case per Findings #5. |
| Reschedule | Partial | Placeholder (069). | Harden DO NOT EXECUTE. |
| Concurrent / inventory | Partial | Concurrent last-ticket (073); but Payment Countdown expiry inventory return + multi-tab same-user race not covered. | Add per Recommended Additions. |
| Compatibility / Multilingual / Regression | Covered | 070-072. | Keep. |

---

## [SECTION] Quality Checklist

- [x] Each case maps to a mindmap leaf, OQ-driven yellow, or cross-cutting concern.
- [x] Preconditions clear.
- [x] Test data defined.
- [ ] Steps specific enough — **TC-069 Reschedule placeholder is vague**; see Findings #6.
- [ ] Expected results observable — **TC-041 verifies absence without driving the product question**; see Findings #1.
- [x] Priority / Severity match risk.
- [x] No duplicates.
- [x] Blocked / Deferred documented.
- [x] Regression considered (072).
- [N/A] Evidence — project template uses Screenshots column at execution time.

---

## [SECTION] Findings

| Severity | Issue | Impact | Suggestion | Owner |
|---|---|---|---|---|
| Major | **TC-041 (Transfer absent on Admission Ticket) is shaped as passive absence verification.** Mindmap 007 has Transfer on Seat Selection Ticket; mindmap 013 does NOT have Transfer on Admission Ticket. TC-041 verifies "Transfer control is ABSENT" — but this codifies an unverified product assumption. Two possible product directions (Transfer is Seat-Selection-only feature; OR mindmap omission and Admission Ticket also gets Transfer) need separate Deferred cases, not a single absence check. | Risk of false-pass when reality matches the case but for wrong reason (omission vs design). Same class of issue caught in login QA2 review TC-035. | Split TC-041 into: (a) TC-041a Deferred — verify Transfer absent per mindmap interpretation; (b) TC-041b Deferred — author Admission Ticket Transfer happy path pending Product confirmation that Admission Ticket should also support Transfer. Mark both yellow rows. (Note: round 2 implemented this as TC-041 paired with TC-078 to avoid mid-ID renumbering.) | QA1 / Product |
| Major | **TC-044 (QR Code "mapping field") semantic mismatch for Admission Ticket.** Mindmap 013 QR Code sub-tree mentions "对应的座位" (corresponding seat), but Admission Ticket has no seat concept. The case correctly notes this as TBD but doesn't drive resolution — what SHOULD an Admission Ticket QR map to? Ticket Number? Ticket Type + serial? Order line item? | Test cannot pass / fail without product semantics. | Either (a) split into a Deferred-pending-product version + an executable version once Ticket Number semantics are confirmed; or (b) leave as Deferred with yellow cell on Expected Result item 3 and flag the Open Question for Product. | QA1 / Product |
| Major | **Inventory return on Payment Countdown expiry is not verified** (same as Seat Selection Ticket review Finding #1). TC-014 verifies countdown but not inventory release. | Inventory leak; revenue loss; customer support spike. | Add TC-074: "Payment Countdown expiry → ticket release verification" (user A lets countdown expire; user B can immediately select the same Ticket Type). | QA1 / Tech |
| Major | **Multi-tab same-user race not covered** (same as Seat Selection Ticket review Finding #2). | Self-double-booking; phantom inventory. | Add TC-075: "Same-user multi-tab same-Admission-Ticket race". | QA1 / Tech |
| Major | **Refund × Add-On interaction not covered** (same as Seat Selection Ticket review Finding #3). | Customer dispute on refund amount; Add-On fulfillment state inconsistency. | Add TC-076: "Refund with Add-On attached — fulfillment-state refund behavior (unshipped vs shipped)". | QA1 / Product |
| Major | **Duplicate ID number across participants in same order not covered** (same as Seat Selection Ticket review Finding #4). | Real-Name fraud / data integrity; compliance risk. | Add TC-077: "Real-Name — duplicate ID number across participants — allowed / blocked / warning". | QA1 / Product |
| Major | **TC-069 Reschedule placeholder step text vague.** Same false-pass risk as Seat Selection Ticket TC-091 and login TC-046/047. | False-positive execution. | Replace step text with explicit `**TBD — DO NOT EXECUTE**` and Expected Result with `Status defaults to Blocked at handoff`. | QA1 |
| Minor | **E-ticket email content elements not explicitly verified** (TC-020 says "email contains QR / UUID / order info" without per-language sender / subject / format). | Email-side regression escapes. | Optional — extend TC-020 or add dedicated case for e-ticket email content elements across languages. | QA1 |
| Minor | **Admission Ticket Sold Out case (TC-049) doesn't distinguish "all Ticket Types sold out" vs "single Ticket Type sold out".** Some Admission events have student / senior / general Ticket Types — one sells out while others remain. | Reduced coverage for mixed-availability Ticket Types. | Optional — extend TC-049 or add a case for mixed-availability Ticket Type display. | QA1 |
| Minor | **Student / Senior / Group-discount Ticket Type eligibility validation not covered.** Mindmap 010 implies Ticket Type differentiation; if some Ticket Types require eligibility proof (student ID / senior ID), validation cases are absent. | Eligibility fraud / dispute. | Optional — confirm with Product whether eligibility-validated Ticket Types exist; if yes, add an eligibility-validation case. | QA1 / Product |
| Minor | **6 payment methods bundled per-method (good); but 5 failure types bundled into TC-037** (same as Seat Selection Ticket review Minor). | Reduced diagnostic isolation. | Optional — split if execution shows different handling. | QA1 |

---

## [SECTION] Recommended Additions

| Suggested Case | Reason | Priority |
|---|---|---|
| TC-041a / TC-041b Transfer absence + Transfer happy-path (Deferred pair) | Closes Major Finding #1; drives Product decision rather than codifying an assumption. (Implemented as TC-041 + TC-078 in round 2.) | High (Deferred pending Product) |
| TC-074 Payment Countdown expiry → ticket release verification | Closes Major Finding #3 (shared with Seat Selection Ticket). | High |
| TC-075 Same-user multi-tab same-Admission-Ticket race | Closes Major Finding #4 (shared with Seat Selection Ticket). | High |
| TC-076 Refund with Add-On attached — fulfillment-state refund behavior | Closes Major Finding #5 (shared with Seat Selection Ticket). | High |
| TC-077 Real-Name duplicate ID across participants | Closes Major Finding #6 (shared with Seat Selection Ticket). | Medium |

---

## [SECTION] Re-Review Status (2026-05-17 round 2)

QA1 revised the case set on 2026-05-17 (revision history row added; case count 73 → 78).

| # | Round-1 Finding | Severity | Status | Evidence |
|---|---|---|---|---|
| 1 | TC-041 (Transfer absence) shaped passively | Major | **Closed** | TC-041 kept as Deferred absence-verification; new TC-078 added as paired Deferred happy-path placeholder pending product direction. Both yellow rows. |
| 2 | TC-044 QR Code "mapping field" semantic mismatch for Admission Ticket | Major | **Closed** | TC-044 Expected Result item 3 yellow-celled (col 11); wording clarified to "Ticket Number / Ticket Type / Order Line Number (not seat)" pending product confirmation. |
| 3 | Payment Countdown expiry → ticket release not verified | Major | **Closed** | TC-074 added — verifies ticket lock release post-countdown across two sessions. |
| 4 | Multi-tab same-user race not covered | Major | **Closed** | TC-075 added (yellow row) — verifies same-user 2-tab same-Admission-Ticket selection per product policy. |
| 5 | Refund × Add-On interaction not covered | Major | **Closed** | TC-076 added (yellow row) — verifies Refund behavior on Admission Ticket order with Add-On across unshipped / shipped states. |
| 6 | Duplicate ID across participants not covered | Major | **Closed** | TC-077 added (yellow row) — verifies duplicate-ID behavior. |
| 7 | TC-069 Reschedule placeholder step text vague | Major | **Closed** | Steps now read `**TBD — DO NOT EXECUTE.**`; Expected: Status defaults to Blocked at handoff. |
| 8 | E-ticket email content elements not explicitly verified | Minor | **Carried** | Optional — extend TC-020 or add dedicated case once language matrix confirmed. |
| 9 | Sold Out case doesn't distinguish "all Ticket Types sold out" vs "single Ticket Type sold out" | Minor | **Carried** | Optional — extend TC-049 if test data permits mixed-availability events. |
| 10 | Student / Senior Ticket Type eligibility validation not covered | Minor | **Carried** | Optional — confirm with Product whether eligibility-validated Ticket Types exist; add case if yes. |
| 11 | 5 failure types bundled into TC-037 | Minor | **Carried** | Optional split (same as Seat Selection Ticket review carried Minor). |

---

## [SECTION] Final Decision

- Decision: **Pass (AI re-review)** — all 6 Majors Closed; 0/5 Minors Closed; 5 Minors Carried as optional polish.
- Reason: Case set now covers the QA2-flagged state-transition (Payment Countdown), self-race (multi-tab), cross-flow (Refund × Add-On), data integrity (ID duplicate), and Admission-Ticket-specific direction items (Transfer paired Deferred; QR Code mapping-field semantics yellow). Placeholder for Reschedule hardened. Total cases 78.
- Follow-up Owner: Product / Tech (resolve all Deferred items: Cybersource, Refund enablement, Refund Handling Fee, Transfer direction, QR Code semantics, multi-tab policy, Refund × Add-On rule, ID duplicate rule); QA1 may pick up Carried Minors as optional cleanup.
- Gate 2 (Test Design Ready): **Satisfied for non-Deferred cases** per Quality Owner direction (no human co-sign step).
