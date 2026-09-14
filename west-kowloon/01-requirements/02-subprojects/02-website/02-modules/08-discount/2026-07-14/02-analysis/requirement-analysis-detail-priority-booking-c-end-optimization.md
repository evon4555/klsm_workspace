# Requirement Analysis Detail - Priority Booking C-end Optimization

Package: `08-discount/2026-07-14`

Formal review document:
`requirement-consolidation-priority-booking-c-end-optimization.md`

Status: Signed-scope analysis companion. The requirement consolidation was
signed off by the Test Manager on 2026-07-15.

## 0. Signed Scope Decisions

| ID | Signed Decision |
|----|----|
| Q-1 | Treat 7/14 as a new requirement evaluation; use 6/25 cases/screenshots as references only. |
| Q-2 | Keep `Partner Benefits` in active scope for validation data sync, viewing, and unbinding. |
| Q-3 | C-end asks users to input the first 8 digits for bank-card validation. |
| Q-4 | Display validation validity period on C-end. |
| Q-5 | Hide the cart icon before public sale; do not use click interception as the main path. |
| Q-6 | Website tests only visible payment success/failure results; CyberSource detailed certification remains payment-side responsibility. |
| Q-7 | Do not test checkout-page "priority qualification used" display. |
| Q-8 | B-side changes are outside this Website C-end package. |
| Q-9 | Old `mid` conflict is regression reference only; no new matrix. |
| Q-10 | No dedicated multilingual / fallback test matrix this round. |

## 1. Source Authority

West Kowloon source authority remains mindmap > PRD > Figma. No mindmap was
provided for this package, so the extracted PRD markdown is the working
authority. Figma and HTML prototypes are reference sources. The prior
2026-06-25 package is a required impact reference, not a template source and
not an authority over the new 2026-07-14 business flow. The document structure
is governed by the shared requirement-consolidation template.

## 2. Integrated Breakdown

| ID | Capability | Trigger / Actor | Expected Outcome | Source |
|----|----|----|----|----|
| F1 | No-priority-booking fallback | User enters a project detail page where no priority booking is configured. | Page shows normal public-sale status and regular purchase entry only; no priority-booking policy area is shown. | PRD BR001, AC-001 |
| F2 | Priority-booking policy area | User enters a project detail page where priority booking is configured. | Page displays the priority-booking area and full configured policies by type. | PRD BR003, BR004, AC-002 |
| F3 | Account identity recognition | System identifies unauthenticated, guest/temporary, or registered user. | Display and operations follow the account-state rules: unauthenticated and guest users see full policy as not matched; registered users get qualification recognition. | PRD account flow, BR019..BR021, AC-003..AC-004 |
| F4 | Priority type grouping | Project has bank-card, membership-card, stored-value-card, or member-level priority booking. | Policies are grouped as bank card, membership card, stored-value card, and member level. | PRD BR003, BR004 |
| F5 | Matched-policy sorting | Registered user has one or more matched priority-booking items. | Matched qualification cards are moved forward; multiple matches sort first by earliest purchasable time, then by bank card > membership card > stored-value card > member level. | PRD BR005, AC-005..AC-006 |
| F6 | Unmatched-policy sorting | Registered user has no matched priority-booking items. | Cards sort by policy purchase time and type priority; if no clear purchase time, backend configuration order is used. | PRD BR006, AC-007 |
| F7 | Status display and visual noise control | Priority cards and items render on P1. | Card-level unified status is shown; matched items use a check icon; item rows do not duplicate "already/ not eligible" text. | PRD BR007, BR008, AC-008 |
| F8 | Bank-card policy card | Bank-card priority booking is configured. | Bank-card item shows qualification name, level information, 1:1 image or logo placeholder, support/exemption text, and per-unmatched-item `立即验证`. | PRD P1 module 3, BR008, BR010, BR018, AC-011..AC-012 |
| F9 | Bank-card validation modal | Registered user clicks `立即验证` on an unmatched bank-card item. | P2 modal opens with important notice, supported range, BIN input, submit/close, and validation result feedback. | PRD P2, BR013..BR018, AC-016..AC-021 |
| F10 | BIN validation input control | User enters a bank-card prefix in P2. | Input allows digits only, requires the first 8 digits, blocks invalid format/length, and permits retry on failure. | PRD BR014, BR016, AC-017..AC-020; signed Q-3 |
| F11 | Validation success and expiry | Entered first-8-digit prefix matches supported range and later reaches validity expiry. | Corresponding bank-card item becomes qualified, C-end displays validation validity period, and later expiry returns item to unverified with `立即验证` shown again. | PRD BR015, BR017, AC-019, AC-022; signed Q-4 |
| F12 | Guest/temporary immediate validation handling | Guest or temporary user clicks bank-card `立即验证`. | System checks for guest unpaid order; if present, asks whether to cancel order and exit guest mode; if absent, exits guest mode and goes to login. | PRD guest flow, BR020..BR021, AC-023..AC-024 |
| F13 | Unauthenticated restricted action handling | Unauthenticated user clicks login-required action. | User is guided to login; after login the project detail page re-identifies qualifications. | PRD BR019, E001 |
| F14 | Membership-card and stored-value-card qualification acquisition | User sees unmatched membership-card or stored-value-card priority booking. | `获取资格` is shown and jumps to the corresponding card-purchase or qualification page according to account state. | PRD P1 module 4, BR009, AC-013..AC-014, AC-025 |
| F15 | Member-level priority booking display | Project configures member-level priority booking. | Member-level policy and recognition result are shown; first release provides no level-up entry. | PRD P1 module 5, BR009, AC-015 |
| F16 | Purchase-entry gating | User clicks purchase entry before or after eligible priority time. | Purchase button and entry behavior are controlled by public-sale status, priority status, purchase qualification, inventory, and project purchase rules. | PRD purchase-entry flow, BR002, BR022..BR023, AC-026..AC-028 |
| F17 | Priority booking without independent inventory | User enters a priority-booking flow. | Priority booking uses public inventory and does not guarantee ticket availability. | PRD BR022, AC-028 |
| F18 | Cart behavior for priority booking | Current channel public-sale time has not arrived. | Priority-booking project does not support cart; cart icon is hidden. | PRD P3 module 3; signed Q-5 |
| F19 | Checkout priority information | Order checkout page has a matched priority-booking qualification. | Dedicated "priority qualification used" display is not covered this round. | PRD P4; signed Q-7 |
| F20 | Payment-stage bank-card recheck | User has passed bank-card pre-validation and enters payment. | Payment stage still requires a matching bank card; real-time issuer/payment-institution checks may fail and should return a failure prompt. | PRD BR018, BR024, AC-029 |
| F21 | Multilingual display | Site language switches among simplified Chinese, traditional Chinese, and English. | No dedicated multilingual / fallback matrix this round. | PRD BR025, AC-030; signed Q-10 |
| F22 | B-side prerequisite changes | Backend config changes support C-end display. | B-side fields such as level-name multilingual support, drawer mode, and usage-condition description are prerequisites/reference unless this package is assigned admin coverage. | PRD P1 module 3 B-side notes |
| F23 | `Partner Benefits` continuity | User needs to view or unbind priority-related identity after project-page validation data sync. | `Partner Benefits` remains in scope for sync/view/unbind coverage, without mechanically reopening the 6/25 old case list. | signed Q-2 |

## 3. Differences vs Previous Version

| ID | Capability | 2026-06-25 Behavior | 2026-07-14 Behavior | Test Impact |
|----|----|----|----|----|
| D-prev-1 | Entry point | Primary C-end user action is personal-center `Partner Benefits` binding, then checkout reads the bound identity. | Primary C-end flow starts from the project detail page priority-booking policy area. | New P1 project-detail cases are required; `Partner Benefits` remains active for validation data sync, viewing, and unbinding. |
| D-prev-2 | Policy scope | Old C-end scope focuses on bank-card / partner-member priority purchase. | New C-end scope displays bank card, membership card, stored-value card, and member level priority booking together. | Add multi-type grouping and cross-type sorting coverage. |
| D-prev-3 | Bank-card validation | Old flow uses identity binding and previous decisions around full card number / BIN matching. | New flow validates bank-card item directly from the project page modal using first-8-digit input and displays validity period. | Rewrite validation cases around P2 modal, status refresh, and validity display. |
| D-prev-4 | Account states | Old cases mostly center logged-in users and personal-center behavior. | New PRD explicitly defines unauthenticated, guest/temporary, and registered users. | Add account-state matrix, especially guest unpaid-order handling. |
| D-prev-5 | Cart behavior | Old workbook includes cart and checkout E2E references. | Priority-booking project does not support cart before public-sale time; signed decision is to hide the cart icon. | Existing cart assertions must be revised or replaced; changed cells/rows should be yellow-highlighted later. |
| D-prev-6 | Purchase gating | Old flow emphasizes checkout benefit decision and quota deduction. | New flow emphasizes purchase-entry gating and transaction-front recheck before event/session/seat/order creation. | Add purchase-entry and transaction-front recheck cases for Admission ticket and seat-selection ticket. |
| D-prev-7 | Payment risk | Old flow includes bank-card priority purchase vs bank-card discount conflict by MID. | New flow says pre-validation does not guarantee payment success; payment-stage card/issuer/payment checks can fail. | Website covers visible success/failure result only; old MID conflict remains reference, no new matrix. |
| D-prev-8 | Quota / refund | Old cases include priority purchase count deduction and refund behavior. | New PRD does not define count deduction or refund reversal. | Treat old quota/refund as regression/open question, not default 7/14 main scope. |
| D-prev-9 | i18n | Old cases cover partner/level rendering in zh-CN, zh-HK, and en. | New PRD covers priority area, modal, prompt, button, and `Priority Booking` wording. | No dedicated multilingual / fallback matrix this round. |
| D-prev-10 | Screenshots | Old workbook contains embedded screenshots/images. | New PRD supplies HTML prototypes and images. | Use old workbook images as visual continuity reference and new prototype/images as current expected layout reference. |

## 4. Differences vs Standard Product

| ID | Capability | Standard / Prior Product Assumption | 2026-07-14 Behavior | Sync Back |
|----|----|----|----|----|
| D-std-1 | Complete priority-booking display | Standard product may show sale status and purchase entry without a unified multi-type priority area. | Website project detail page must show complete policies by type. | TBD |
| D-std-2 | Priority qualification entry | Standard product may treat qualification acquisition outside project detail. | C-end project detail page includes `立即验证`, `获取资格`, login guidance, and guest handling. | TBD |
| D-std-3 | Bank-card pre-validation notice | Standard bank-card validation might imply eligibility. | PRD explicitly warns validation only grants entry to priority flow and does not guarantee payment success. | Likely product rule |
| D-std-4 | Cart behavior | Standard ticketing pages may support cart. | Priority-booking projects before public sale hide the cart icon. | Project/product decision needed |
| D-std-5 | Multilingual wording | Standard wording may vary. | English display uses `Priority Booking`; simplified/traditional/English prompts are expected. | Not a dedicated test matrix this round |

## 5. Differences vs Adjacent Modules

| ID | Adjacent Module | Impact |
|----|----|----|
| D-adj-1 | Ticketing | Project detail page, event/session entry, admission-ticket purchase, seat-selection purchase, inventory, and purchase qualification must obey priority gating. |
| D-adj-2 | Cart | Cart icon is hidden for priority-booking projects before public-sale time. |
| D-adj-3 | Payment | Bank-card priority purchase requires payment-stage bank-card condition recheck and failure prompt. |
| D-adj-4 | Login / Guest | Unauthenticated login redirect and guest/temporary exit flow affect pending unpaid guest orders. |
| D-adj-5 | Membership Card / Stored-value Card | `获取资格` jump destination and qualification state must integrate with card ownership or purchase pages. |
| D-adj-6 | i18n | No dedicated multilingual / fallback matrix this round. |
| D-adj-7 | Backend/Admin | B-side fields and policy configuration provide test data but full admin CRUD ownership is unclear. |

## 6. Test Scope This Round

### In Scope After Sign-Off

| Capability | Scope Statement |
|----|----|
| F1-F2 | Project detail behavior with and without priority booking configured. |
| F3 | Account-state display and action behavior for unauthenticated, guest/temporary, and registered users. |
| F4-F7 | Four priority types, grouped display, matched/unmatched sorting, status display, and noise-control behavior. |
| F8-F11 | Bank-card priority card, validation modal, first-8-digit input validation, success/failure/retry/close, status refresh, validity display, and expiry handling. |
| F12-F13 | Guest/temporary immediate-validation flow and unauthenticated login flow. |
| F14-F15 | Membership-card / stored-value-card `获取资格` and member-level display-only behavior. |
| F16-F18 | Purchase-entry gating, no independent inventory, Admission ticket and seat-selection ticket split, and cart hidden behavior. |
| F20 | Payment-stage bank-card recheck / failure prompt as Website-visible result only. |
| F23 | `Partner Benefits` sync/view/unbind coverage related to project-page validation. |
| Prior reference | Use 2026-06-25 cases and workbook images as reference; future changed cells/rows must be yellow-highlighted. |

### Out of Scope / Deferred By Default

| Capability | Reason |
|----|----|
| Full app / mini-program coverage | PRD says this version covers Website C-end only. |
| Full B-side/admin CRUD | B-side changes are outside this Website C-end package per signed Q-8. |
| Full payment-provider certification | PRD defines customer-facing payment-stage consequence, not payment-institution certification. |
| Full quota/refund rewrite from 2026-06-25 | 7/14 PRD does not define quota/refund behavior. |
| Full old `Partner Benefits` case-list migration | Q-2 keeps related sync/view/unbind paths in scope, but 6/25 cases are not mechanically reopened. |
| Checkout-page "priority qualification used" display | Excluded per signed Q-7. |
| Dedicated multilingual / fallback matrix | Excluded per signed Q-10. |
| Figma pixel-level validation | Figma URL is captured but detailed MCP design context has not been fetched. |

## 7. Resolved Items

| ID | Source Location | Previous Ambiguity | Signed Resolution |
|----|----|----|----|
| U-1 | Project source authority | No mindmap is available for this package. | Treat PRD markdown as working authority and Figma/prototypes as references. |
| U-2 | PRD P2 vs configuration table | BIN input is described as activity-configured/default 6 digits in one place and fixed first 8 digits in another. | C-end uniformly asks for first 8 digits per signed Q-3. |
| U-3 | BR015 vs prototype | BR015 says C-end does not display validation duration; prototype says validation result is valid for 1 day. | C-end displays validation validity period per signed Q-4. |
| U-4 | Old 6/25 flow relationship | PRD does not state whether `Partner Benefits` remains, is replaced, or coexists. | Keep sync/view/unbind in active scope per signed Q-2. |
| U-5 | Cart behavior wording | PRD allows hiding cart icon or intercepting click. | Hide cart icon per signed Q-5. |
| U-6 | P4 checkout UI | PRD says P4 UI design is todo. | Do not test checkout priority-used message per signed Q-7. |
| U-7 | B-side notes | B-side field changes appear inside C-end PRD. | B-side changes are outside this Website C-end package per signed Q-8. |
| U-8 | Payment-stage failure | PRD defines failure prompt but not test data or exact third-party error code mapping. | Website test verifies visible failure handling; payment-team verifies provider rule details. |
| U-9 | Old MID conflict | 7/14 PRD does not repeat 6/25 bank-card priority purchase vs bank-card discount MID conflict. | Keep as regression reference only; no new matrix per signed Q-9. |
| U-10 | Multilingual fallback | PRD says multilingual display but not fallback. | No dedicated multilingual / fallback matrix per signed Q-10. |

## 8. Signed Answers

| ID | Question | Options | Owner | Answer |
|----|----|----|----|----|
| Q-1 | Package classification and old-case handling | (a) Treat 7/14 as new requirement evaluation, using 6/25 cases/screenshots as reference only; (b) reopen and directly update 6/25 cases; (c) produce both a new package and a 6/25 maintenance branch | Test Manager | a |
| Q-2 | Relationship to `Partner Benefits` | (a) Regression/reference only; (b) still active scope in 7/14; (c) replaced by project-detail validation and should be deprecated later | Product / Test Manager | b, project-page validation does data sync; viewing/unbinding still goes through `Partner Benefits`. |
| Q-3 | BIN input length | (a) Activity-configured length, default 6 digits; (b) fixed first 8 digits; (c) support both depending on activity config and display rule | Product / Dev | C-end uniformly asks users to enter the first 8 digits. |
| Q-4 | Should C-end display validation validity period? | (a) No, hide duration per BR015; (b) yes, show duration such as 1 day per prototype; (c) configurable copy | Product / Design | b, display it so users know when it expires. |
| Q-5 | Cart behavior for priority-booking project before public sale | (a) hide cart icon; (b) show cart icon but intercept click; (c) either behavior is acceptable by channel/config | Product / Dev | a, priority booking is unrelated to cart. |
| Q-6 | Payment-stage validation test boundary | (a) Website tests only visible success/failure handling with prepared payment data; (b) Website owns detailed card/issuer/provider matrix; (c) split website UI and payment-team certification | Test Manager / Payment owner | a, detailed behavior is CyberSource/payment side. |
| Q-7 | P4 checkout priority-used message | (a) In scope this round despite UI todo; (b) defer until UI is ready; (c) verify only through backend/order data | Product / Design | b, checkout page should not display this message. |
| Q-8 | B-side changes ownership | (a) Admin teams own full config CRUD; this package covers C-end only; (b) include B-side test cases here; (c) create separate admin package | Test Manager | a |
| Q-9 | Old 6/25 MID conflict regression | (a) Keep old conflict rule as regression reference but no new matrix; (b) include explicit regression cases in 7/14; (c) ask product to restate coexistence rule first | Product / Test Manager | a, no conflict is expected. |
| Q-10 | Multilingual fallback | (a) Use zh-CN fallback as in 6/25; (b) use English fallback; (c) show empty/key; (d) defer fallback and test only configured translations | Product / Test Manager | No dedicated multilingual / fallback testing is needed. |

## 9. Hand-Off Statement

The requirement consolidation is signed off. `03-test-design` will produce
`test-cases-priority-booking-c-end-optimization.md` and `.xlsx` using the
project workbook template, with prior 2026-06-25 cases/screenshots as required
references. The resulting workbook must follow the 7/14 business flow, apply
Admission ticket vs seat-selection ticket split where applicable, and
yellow-highlight cells or rows whose meaning changed from the previous
reference.
