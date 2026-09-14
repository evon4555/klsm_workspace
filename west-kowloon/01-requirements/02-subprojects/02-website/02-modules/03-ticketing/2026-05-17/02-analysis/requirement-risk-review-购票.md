# Requirement Risk Review

---

## [SECTION] Revision History

| Date | Reviewer | Change |
|---|---|---|
| 2026-05-17 | AI QA (QA2 role) | Initial draft based on mindmap 001–014 + figma link + project layer (`project-context.md`, `在线购票.pdf` referenced as supplementary). Scope covers homepage + ticket purchase E2E. |
| 2026-05-17 | AI QA (QA2 role) — Round 3 | Terminology standardization per `D:/Workspace/qa-harness/03-context/company/01-source-documents/terminology/AnTank系统的行业术语库.xlsx`. User-specified naming overrides: 座票 → **Seat Selection Ticket**, 门票 → **Admission Ticket**. All Chinese-mixed wording replaced with Working English; mindmap node names retained only in source citations. |

---

## [SECTION] Requirement Summary

- **Business goal**: Enable a Website visitor to browse an event detail page (homepage) and complete a ticket purchase end-to-end — Date Selection / Seat Selection or Ticket Selection / Order Confirmation / Payment via Cybersource / Order Detail with e-ticket receipt — with refund and reschedule capability and optional Merchandise Add-On for single-ticket-type orders.
- **Main change**: 2026-05 dry-run scope expanded beyond authentication (login package) to cover the **purchase user journey**. Two ticket-type variants: **Seat Selection Ticket** (reserved seating, full seat-map selection) and **Admission Ticket** (general admission, ticket-type selection).
- **Affected users**: Registered Website users (the only users who can purchase per mindmap 008/014 add-on rule "仅注册用户可以加购"); guest users likely blocked from purchase flow (TBD per Open Question — verify against guest permission cases from login package TC-025).
- **Affected systems**: Website frontend, account service, inventory / seat-lock service, pricing engine (Discount / Service Fee / Charity Donation), Cybersource payment gateway (6 payment methods), email / e-ticket service, refund workflow + approval engine, order management, Real-Name Verification service (6 ID types), shopping cart, Merchandise Add-On inventory + Delivery / Self Pickup fulfillment.
- **Source basis**: Mindmap source PNGs under `..\01-input\02-mindmap\` are authoritative. PRD `..\..\..\..\..\01-source-documents\02-prd\2026-05-14\国际版标准官网 - 在线购票.pdf` is supplementary reference. Source-authority order: **mindmap > PRD** (project default). PRD-fills-gap rule applies. Combo Ticket / Cross-Session Bundle Ticket are figma-only (mindmap absent) → treated as yellow placeholder pending scope decision.

---

## [SECTION] Sub-Package Decomposition

Per Quality Owner direction 2026-05-17, scope split into 3 sub-folders under `..\03-test-design\`:

| Sub-package | Mindmap source | Scope |
|---|---|---|
| `01-homepage\` | 001 + 002 top-level | Event detail page (Wishlist / Share / View Discounts / Venue / Service Notes / Overview / Event Information / Event Images / Buy Tickets entry / Same-Venue Related Events / Service Guarantees / Recommended Events) + Buy Tickets entry routing (Seat Selection Ticket / Admission Ticket split). Includes yellow placeholders for Combo Ticket + Cross-Session Bundle Ticket (figma-only). |
| `03-seat-selection\` | 003–008 + 002 Refund/Reschedule | Seat Selection Ticket main flow (Date Selection / Seat Selection / Order Confirmation / Payment / Order Detail / Other) + Merchandise Add-On (Seat variant) + Refund (Seat variant) + Reschedule (Seat placeholder). |
| `02-ticketing\` | 009–014 + 002 Refund/Reschedule | Admission Ticket main flow (same structure as Seat Selection Ticket minus seat-map) + Merchandise Add-On (Admission variant) + Refund (Admission variant) + Reschedule (Admission placeholder). |

Cross-package note: Add-On / Refund / Reschedule logic is shared between Seat Selection Ticket and Admission Ticket, but cases are **written separately per ticket type** (each package owns its own complete set). Rationale: independent execution per ticket type, no cross-package dependencies.

---

## [SECTION] Open Questions

Items with `?` or yellow / red highlight in mindmap, plus user-flagged scope items. Authoritative list (test case sub-packages reference this section).

| Priority | Question | Why It Matters | Owner | Source |
|---|---|---|---|---|
| High | **Cybersource integration scope** — sandbox availability in SIT? Are all 6 payment methods (Visa / Master / JCB / CUP / Apple Pay / Google Pay) testable? Which "other payment failure" cases require Cybersource direct confirmation (red node 006/012)? | Determines whether payment-layer cases execute in dry-run or stay Deferred. | Tech / Cybersource | Mindmap 006/012 red+yellow |
| High | **2-step payment confirmation trigger conditions** — "triggered under specific conditions" — what conditions? | Cannot author negative / boundary cases for 2-step confirm without knowing the trigger. | Product / Tech | Mindmap 006/012 yellow |
| High | **Refund conflict with Order Detail message** — 007/013 say "per sales policy, West Kowloon generally disallows refund", but 002 details a full refund workflow (conditions / approval / refund failure or success / User Withdraw). Is refund enabled for this dry-run, disabled, or partial (specific event types only)? | Determines whether full refund test set executes or stays Deferred. | Product | Mindmap 002 vs 007/013 conflict |
| High | **Refund Handling Fee configuration** — config location + calculation method + accumulation rule when same order refunds different tickets multiple times. | Refund-fee cases cannot pass/fail without rule. | Product / Tech | Mindmap 002 yellow |
| High | **Reschedule rules** — completely undefined in mindmap (just a leaf node). | Cannot author beyond a placeholder yellow row per ticket type. | Product | Mindmap 002 Reschedule (leaf only) |
| High | **Combo Ticket / Cross-Session Bundle Ticket in scope?** — figma has them, mindmap doesn't. Quality Owner direction: write 1 yellow placeholder each in homepage sub-package. | Determines whether to expand or keep as 2 placeholders. | Product | Figma only |
| High | **Add-On cross-rule "mixed cart blocks add-on"** — confirmed by user 2026-05-17. Need exact UX: show a message? disable add-on button? block at checkout? | Determines expected result wording for the cross-rule case. | Product | User direction |
| High | **Service Fee** — where configured / how calculated (including discount + delivery context) / whether multiple types (percentage / fixed / waived above threshold). | Pricing cases cannot pass/fail without rule. | Product / Tech | Mindmap 005/011 yellow |
| High | **Discount rules** — 005/011 yellow on "Discount" — types / stacking / display. | Pricing / Order Summary cases blocked. | Product | Mindmap 005/011 yellow |
| Medium | **Payment Countdown duration configurable?** — exact Order Confirmation page timeout. | Payment Countdown case execution. | Product / Tech | Mindmap 005/011 |
| Medium | **Phone validation rules** — has validation? international format check method? | Contact Information negative cases. | Product / Tech | Mindmap 005/011 |
| Medium | **Venue map** — popup location pin? what map provider (Google / Gaode / Apple)? | Venue case behavior + provider sandbox needs. | Product / Tech | Mindmap 001 |
| Medium | **ID validation + display masking** — 6 ID types' per-type validation + display masking format. | Real-Name negative + privacy cases. | Product / Tech | Mindmap 004/010 |
| Medium | **System-Assisted Seat Selection** — feature scope: algorithm / user control / cancel-and-reselect? | Decide whether to test independently or merge into selected-seat case. | Product | Mindmap 004 yellow |
| Medium | **Transfer (ticket transfer)** — only on Seat Selection Ticket Order Detail (007), absent on Admission Ticket (013). Is this deliberate (Seat-Selection-only feature) or mindmap omission? | Decide whether Admission Ticket sub-package needs Transfer cases. | Product | Mindmap 007 yellow vs 013 missing |
| Medium | **Multi-ticket refund — handling fee accumulation** | Refund fee case combinatorics. | Product / Tech | Mindmap 002 yellow |
| Medium | **Refund approval — rejected → second refund request allowed?** | Refund negative path. | Product | Mindmap 002 yellow |
| Medium | **Refund approval — User Withdraw mid-process** | Refund cancellation case. | Product | Mindmap 002 yellow |
| Medium | **Add-On E-voucher Coupon fulfillment** — how does coupon fulfillment differ from Delivery / Self Pickup? | Add-on fulfillment cases. | Product | Mindmap 008/014 add-on |
| Medium | **Add-On Delivery Prepaid — "extra delivery fee even though ticket already covered delivery"** — exact rule + UX wording | Add-on payment cases. | Product | Mindmap 008/014 add-on |
| Medium | **Event Image precision + multi-image display** — detail page image handling rules | UI / compatibility cases. | Product / Tech | Mindmap 001 |
| Medium | **Same-Venue Related Events / Recommended Events — recommendation logic?** | Recommendation cases. | Product | Mindmap 001 |
| Medium | **"No Electronic Invoice" (Service Notes)** — is this product-confirmed (declaration) or pending product decision? | Decide Service Notes case wording (assertion vs open question). | Product | Mindmap 001 |
| Medium | **Figma "Top rate" element — source?** — 001 explicit "?" node | UI element source — decide whether to test. | Product / Design | Mindmap 001 |
| Medium | **Multilingual scope** | General — carried from login package | Product | Carry-over from login package |
| Medium | **Can guest users purchase?** — Login package TC-025 restricts guest from personal centre / wallet / order management — is Buy Tickets entry also blocked for guest? | Determines guest-flow purchase cases. | Product | Cross-package from login |
| Low | **Event Image precision + multi-image upper bound** | UI polish | Product / Design | Mindmap 001 |

---

## [SECTION] Risk Review

| Risk Area | Risk | Impact | Suggested Test Focus |
|---|---|---|---|
| Business | Users cannot complete a ticket-purchase E2E flow during dry-run. | Revenue blocked; admission system has no validated end-to-end path. | P0: each ticket type's main flow (Date Selection → Seat/Ticket Selection → Order Confirmation → Payment Success → Order Detail); homepage Buy Tickets entry routing. |
| Inventory / seat locking | Concurrent Seat Selection may double-book; abandoned orders may keep seats locked indefinitely; refund may not return inventory. | Overselling, ghost-held seats, customer disputes. | Concurrent Seat Selection on same seat; cart-abandon + auto-release; refund success → inventory return; "Unlocked Seat" reminder (mindmap 004) behavior. |
| Pricing | Service Fee / Discount / Charity Donation / Coupon may miscalculate, especially under stacking, Delivery, large-order-fee-waiver conditions. | Wrong charges, customer disputes, refund volume spike. | Order Summary amount validation per pricing rule combinatorially; backend cross-check (mindmap repeats "compare with backend"); Service Fee multiple-type cases (percentage / fixed / large-order-waiver). |
| Payment integration | Cybersource failure modes (5 known + "other"); 2-step confirm trigger ambiguity; payment gateway downtime; double-charge under retry. | Payment lost, double-charge, customer support spike. | Each of 5 failure types (Insufficient Funds / Bank Declined / Card Expired / Lost or Stolen Card / Credit Limit Exceeded); 2-step confirm trigger (Deferred — condition TBD); duplicate submit; gateway timeout. |
| Real-Name compliance | Real-Name required ticket types not enforced; OR 6 ID types validation missing / inconsistent; OR PII not masked, exposed in clear text. | Compliance breach, identity exposure. | Real-Name ticket-type mandatory enforcement; per-ID-type input validation; masking display correctness; Set-as-Self auto-fill; Edit / Delete participant. |
| Refund workflow | Multi-state workflow (conditions / detail page / handling fee / approval Approved/Rejected / Refund Process Success/Failure / User Withdraw) — easy to leave a state untested; refund-fee calculation under multi-ticket refund ambiguous. | Customer money stuck, double-refund, wrong fee. | State coverage per workflow node; 4 refund conditions (mindmap 002); fee calculation matrix; withdraw timing (already-approved vs in-progress); multi-ticket-refund fee combinatorics. |
| Add-On cross-rule | Mixed cart (Seat Selection + Admission in same order) must block Merchandise Add-On; pure single-type must allow it. | Customer confusion, system inconsistency, business rule violation. | **Critical cross-rule case**: build mixed cart → verify add-on disabled / blocked; pure Seat Selection → add-on works; pure Admission Ticket → add-on works; registered-user-only enforcement; adjustable quantity; Fulfillment Methods (Delivery prepaid rule / Self Pickup / E-voucher Coupon). |
| Authentication interaction | Purchase requires authenticated user (per add-on rule); login package's auth state must hand off correctly into purchase flow. | Guest-blocked-but-then-allowed regression; session expiry mid-checkout loses cart. | Regression: login → Buy Tickets entry; logout-during-checkout; session timeout on Order Confirmation page (Payment Countdown case); login-as-different-user mid-flow. |
| Combo Ticket / Cross-Session Bundle Ticket | Out of mindmap; 1 yellow placeholder per (homepage). Untested at present. | Scope drift if these turn out to be in dry-run. | Yellow placeholder cases — 1 per (Combo Ticket, Cross-Session Bundle Ticket) — pending scope decision. |
| Reschedule | Completely undefined in mindmap. | Untestable; if shipped without spec, escapes detection. | 1 yellow placeholder per ticket type (Seat Selection, Admission). |
| Transfer | Mindmap shows on Seat Selection Ticket only; Admission Ticket absent. May be deliberate or omission. | Either Admission Ticket Transfer missing tests, or Seat Selection Transfer incorrectly added. | Seat Selection Ticket: full Transfer case set; Admission Ticket: 1 yellow placeholder ("verify product intent"). |
| Compatibility | Auth + purchase forms span desktop + mobile + multilingual; payment iframe (Cybersource) may break on mobile. | High-friction entry-to-conversion failure. | Mobile viewport for Seat Selection + Order Confirmation + Payment; multilingual on Order Summary / Privacy / error messages / email; payment iframe rendering. |
| Service Notes | "No Electronic Invoice" is in mindmap as a feature note. If wrong, customers cannot expense purchases. | Customer complaint, compliance issue per region. | Verify "No Electronic Invoice" display matches product intent; confirm declaration accuracy. |
| Recommendation / Same-Venue Related Events | Recommendation logic undefined; could show wrong / stale content. | Customer confusion, low conversion. | 1 case per recommendation block — verify "shows something coherent" + Open Question on algorithm spec. |

---

## [SECTION] Edge Cases And Negative Scenarios (cross-flow highlights)

Detailed coverage lives in each sub-package's test case file. Cross-flow highlights:

- Concurrent purchase: 2 users select same seat (Seat Selection); 2 users add last 1 ticket to cart simultaneously (Admission Ticket).
- Session expiry mid-checkout: Payment Countdown expires on Order Confirmation page → cart cleared / cart restored / partial restore behavior.
- Network failure during payment redirect to Cybersource → user state on return (pending / failed / unknown).
- Refund initiated on order with add-on already shipped — add-on refunded or not?
- Refund approval pending → user attempts new refund on same order → blocked? queued?
- Real-Name ticket with valid passport at purchase, but passport expires before event → admission impact (out of purchase scope; flag as note).
- Mixed cart (Seat Selection + Admission) → user attempts add-on → must be blocked with clear message.
- Email ticket pickup method selected, but user provides invalid email → fail / partial-success / dup-send behavior.
- Apple Pay / Google Pay underlying card invalid → fallback path.
- Payment Countdown setting at 0 / very small / very large → guard rails.
- Multi-language switching mid-checkout → cart / form values preserved? localized correctly?

---

## [SECTION] Recommendation

- Requirement readiness: **Needs Clarification** — 26 Open Questions, several Cybersource- and refund-related items are blocking for execution.
- Recommended risk level: **High** (revenue-critical, payment integration, refund workflow complexity, Real-Name compliance).
- Next action:
  1. Resolve High-priority Open Questions before manual execution starts (Cybersource scope, Refund enablement, Refund Handling Fee rule, add-on cross-rule UX, Service Fee / Discount rules).
  2. For other Open Questions (Medium priority): proceed with case authoring; mark dependent cases / cells **yellow + Deferred** per project mindmap-`?` convention; do not block on these.
  3. Author cases per the 3 sub-package decomposition (`..\03-test-design\{01-homepage, 02-ticketing, 03-seat-selection}\`).
  4. After case authoring, run QA2 review per sub-package (3 review files under `..\04-test-case-review\`).
  5. Confirm Combo Ticket / Cross-Session Bundle Ticket scope decision; expand or keep as placeholders accordingly.
  6. Cross-flow regression vs login package: ensure login → Buy Tickets entry → Seat / Ticket Selection → Order Confirmation hand-off works for registered users; guest behavior to be confirmed per Open Question.
