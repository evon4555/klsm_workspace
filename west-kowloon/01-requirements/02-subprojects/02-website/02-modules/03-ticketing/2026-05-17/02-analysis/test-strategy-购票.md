# Test Strategy

---

## [SECTION] Basic Information

- Project: West Kowloon Website
- Feature / Release: 2026-05-17 dry-run — Homepage (Event Detail Page) + Ticket Purchase E2E (Seat Selection Ticket / Admission Ticket main flows + Merchandise Add-On + Refund + Reschedule placeholder)
- Requirement Link: `..\01-input\input-index.md`; mindmap 001–014; PRD `..\..\..\..\..\01-source-documents\02-prd\2026-05-14\国际版标准官网 - 在线购票.pdf`
- Version / Build: TBD (SIT)
- Owner: Antank QA Team
- Reviewers: Product / BA / Tech Lead / QA Lead
- Date: 2026-05-17
- Risk Level: **High**

---

## [SECTION] Business Context

### [FIELD] Business Goal

Enable a registered Website user to discover an event (homepage), select a ticket-type variant (Seat Selection Ticket — reserved seating with seat-map selection; or Admission Ticket — general admission with ticket-type selection), complete order configuration, pay via Cybersource, receive an e-ticket, optionally add a Merchandise Add-On, and request a Refund or Reschedule post-purchase.

### [FIELD] User Impact

This is the **revenue-critical user journey** for the West Kowloon Website. It depends on the Login package (auth state hand-off) and feeds downstream personal centre / wallet / order management. Failures break the entire B2C sales channel.

### [FIELD] Critical Business Flows

- **Flow A (Homepage)**: User lands on event detail page; can add to Wishlist, Share, View Discounts, browse details, click into Buy Tickets.
- **Flow B (Seat Selection Ticket main)**: Date Selection → Seat Selection (with Real-Name Verification) → Order Confirmation → Payment → Payment Success → Order Detail.
- **Flow C (Admission Ticket main)**: Date Selection → Ticket Selection (with Real-Name Verification) → Order Confirmation → Payment → Payment Success → Order Detail.
- **Flow D (Merchandise Add-On)**: Pure single-ticket-type order → choose add-on SKU → choose Fulfillment Method (Delivery / Self Pickup / E-voucher Coupon) → pay.
- **Flow E (Refund)**: Order Detail → Request Refund → Refund Detail Page → Refund Approval (Approved → Refund Process → Success/Failure; Rejected; User Withdraw).
- **Flow F (Reschedule)**: Placeholder — Reschedule rules undefined; yellow per ticket type.
- **Flow X (cross-rule)**: Mixed cart (Seat Selection + Admission in same order) blocks Merchandise Add-On.

---

## [SECTION] Test Scope

### [FIELD] In Scope

- Homepage event detail elements (Wishlist / Share / View Discounts / Venue / Service Notes / Overview / Event Information / Event Images / Buy Tickets entry / Same-Venue Related Events / Service Guarantees / Recommended Events).
- Seat Selection Ticket flow: Date Selection (calendar / list toggle), Seat Selection (seat map / seat list / Real-Name Verification / 6 ID types / 7 special-seat categories: Wheelchair Seat / Companion Seat / Whole-Table / Obstructed-View Seat / Aisle-Adjacent / Mixed Seating / System-Assisted Seat Selection — yellow).
- Admission Ticket flow: Date Selection, Ticket Selection (price list + Ticket Type list + Real-Name Verification).
- Order Confirmation page (both ticket types): Payment Countdown / Seat List or Admission Ticket List / Contact Information / Ticket Pickup Method / Charity Donation / Order Summary (Discount / Privacy Terms / Service Fee).
- Payment (Cybersource): 6 payment methods (Visa / Master / JCB / CUP / Apple Pay / Google Pay); 5 failure types + "Other failures — needs Cybersource confirmation" (red); 2-step confirmation (yellow); Payment Success page (8 fields).
- Order Detail (both): Order ID / Order Status / Ticket Details / Contact Information / Ticket Pickup Method / Order Info (Payment Reference Number, Payment Method) / QR Codes (multiple QR codes per multi-ticket order) / Order Summary / Request Refund / Reschedule. Seat Selection Ticket includes Transfer (yellow); Admission Ticket — Transfer absent (yellow placeholder pending product).
- Other (008/014): Bundle Ticket (yellow placeholder, scope TBD) / Sold Out / Selling Soon / Ticket Type Remarks / Same-day single & multi-session scenarios.
- Merchandise Add-On (each ticket type writes its own set): registered-user-only / pure-single-ticket-type orders only (mixed cart blocks) / adjustable quantity / 3 Fulfillment Methods (Delivery [Pay on Delivery / Prepaid] / Self Pickup / E-voucher Coupon) / address reused from personal centre.
- Refund (each ticket type writes its own set): 4 refund conditions / Refund Detail Page / Refund Handling Fee / 4-state approval workflow.
- Reschedule (each ticket type writes its own set): 1 yellow placeholder per ticket type.
- Combo Ticket / Cross-Session Bundle Ticket: 1 yellow placeholder each in homepage sub-package (figma-only, mindmap absent).
- Form validation / loading states / duplicate-submit prevention.
- Mobile viewport sanity for Seat Selection / Order Confirmation / Payment.
- Multilingual on error messages, Order Summary, Privacy Terms, email content (cross-cutting case + spot checks).

### [FIELD] Out Of Scope

- Backend admin: backend configuration (Service Fee / Discount / Payment Countdown / Ticket Price / Refund Handling Fee / recommendation algorithm) — tested **against** but not configured by QA.
- Cybersource sandbox provisioning and provider-side bug fixing.
- News Centre / other Website features beyond ticketing.
- Venue map provider confirmation (Open Question — what map provider).
- Performance / load testing (separate plan if release-gating).
- Security penetration testing (separate plan; functional security covered).
- Production fulfillment (actual Delivery / Self Pickup logistics) — verify UI / data flow only.
- Combo Ticket / Cross-Session Bundle Ticket deep coverage (placeholders only).
- Reschedule deep coverage (placeholders only until rules confirmed).

---

## [SECTION] Test Types

| Test Type | Applicability | Notes |
|---|---|---|
| Functional | All sub-packages | Primary type; manual execution in SIT. |
| Integration | Cybersource / email / inventory / Real-Name Verification / refund audit | Cybersource cases gated on sandbox availability; others via SIT data. |
| Negative | All sub-packages | Each main-flow case has its negative-permutation counterpart (similar to login package's error-matrix approach). |
| Compatibility | Selected screens (mobile viewport) | Sanity-level; not full matrix. |
| Multilingual | Cross-cutting | One dedicated case + spot-check notes on individual cases. |
| Regression | vs login package | Auth state → purchase entry hand-off; logout mid-checkout. Spot regression of guest restrictions (login TC-025 extension to purchase routes). |
| Real-Name compliance | Real-Name-required ticket types | 6 ID type input validation + display masking; flagged for legal/compliance review. |
| Anti-abuse | Concurrent seat selection, duplicate submit, Refund withdraw timing | Race-condition probes. |

---

## [SECTION] Role Assignment

| Role | Owner |
|---|---|
| QA1 (functional case authoring / execution / evidence) | Antank QA Team |
| QA2 (requirement risk review, test case review) | Antank QA Lead (currently AI-acting per Quality Owner direction — no human co-sign required for this dry-run) |
| Quality Owner | User |
| Performance QA / Security QA | Out of scope for this dry-run — separate passes if release-gating |

---

## [SECTION] Environment Plan

- **SIT**: Primary target. Web + Cybersource sandbox + email delivery + inventory + Real-Name Verification service required.
- **UAT**: Not in scope for this dry-run.
- **PROD**: Not in scope.

**Environment-dependent Deferred:**
- All Cybersource cases pending sandbox confirmation.
- Apple Pay / Google Pay require device-side configuration; may be Deferred.
- WeChat Pay / Alipay-like local payment if added later — currently mindmap does not list (only listed: Visa / Master / JCB / CUP / Apple Pay / Google Pay).
- HK-specific payment instruments (per Kasi project context): pending HK-side environment.

---

## [SECTION] Test Data Plan

- Registered user accounts (active, with previously-saved Real-Name participants of each ID type) — 6 accounts minimum.
- Test events: 1 Seat-Selection-Ticket-selling event; 1 Admission-Ticket-selling event; 1 with overlapping schedule (same-day single + same-day multi-session); 1 Selling Soon; 1 Sold Out (read-only verification).
- Sample seat maps with each special-seat category configured (Wheelchair / Companion / Whole-Table / Obstructed-View / Aisle-Adjacent / Mixed Seating / System-Assisted if available).
- Cybersource test cards covering all 5 failure types + 6 payment-method success cases.
- Refund-policy-enabled events for Refund execution; refund-disabled events to verify sales-policy-disabled cases.
- Merchandise Add-On catalog with each Fulfillment Method (Delivery Pay-on-Delivery / Delivery Prepaid / Self Pickup / E-voucher Coupon).
- Two languages minimum for multilingual cases.

---

## [SECTION] Regression Scope

- Login package interactions: registered login → homepage → Buy Tickets entry → checkout completes without forced re-login. Guest restriction extension to purchase routes.
- Logout during checkout: cart preserved or cleared per product rule.
- Payment Countdown expiry during checkout: cart / form state.

---

## [SECTION] Automation Opportunity

Out of scope for this dry-run drafting phase. Candidates for later automation:

- Main happy-path per ticket type (P0 regression).
- Seat Selection concurrent-booking probe (would benefit from automation due to timing).
- Cybersource payment-method matrix.

---

## [SECTION] Non-Functional Test Needs

- Performance: handle ≥ moderate concurrent booking under typical event-launch spike — **separate performance plan recommended**.
- Security: payment data handling, Real-Name PII protection, refund-side anti-abuse, session security during checkout — **functional coverage only here**; separate security checklist recommended.

---

## [SECTION] Major Risks And Mitigations

| Risk | Mitigation |
|---|---|
| Cybersource sandbox not ready in time | Author all payment cases; mark all Deferred pending sandbox; do not block other case authoring. |
| 26 Open Questions, several blocking | Author dependent cases with yellow cells / yellow rows; do not block authoring; resolve incrementally with Product. |
| Volume: ~210 cases across 3 sub-packages | Split into 3 sub-folders under 03-test-design (independent QA2 reviews); use shared `regenerate_xlsx.py` for xlsx generation per sub-folder. |
| Refund workflow ambiguity | Author state-by-state cases; mark Deferred where state behavior unknown; surface in Open Questions per sub-package. |

---

## [SECTION] Entry Criteria

- Mindmap PNGs and figma links available in `..\01-input\`. ✅
- Company terminology glossary read (`D:/Workspace/qa-harness/03-context/company/01-source-documents/terminology/AnTank系统的行业术语库.xlsx`) — Working English applied consistently across deliverables. ✅
- Project context (`project-context.md`) reviewed for source authority + PRD layout + 19-col template. ✅
- 02-analysis (this strategy + risk review) drafted. ✅
- Sub-package decomposition agreed (homepage / Seat Selection Ticket / Admission Ticket). ✅

## [SECTION] Exit Criteria (Gate 2 — Test Design Ready)

- 3 test case sets authored under `..\03-test-design\{01-homepage, 02-ticketing, 03-seat-selection}\`.
- 3 QA2 review files under `..\04-test-case-review\`.
- All findings either Closed or carried as Deferred / Carried with explicit owner.
- Per Quality Owner direction 2026-05-17: no human QA2 co-sign required for this dry-run; AI re-review Pass is sufficient to satisfy Gate 2 for non-Deferred cases.
