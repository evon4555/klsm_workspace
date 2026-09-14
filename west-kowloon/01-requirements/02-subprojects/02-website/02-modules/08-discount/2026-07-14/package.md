# Package 2026-07-14

Module: Discount and Member Benefits

Package date: 2026-07-14

Package type: requirement-change-as-new-evaluation

Current status: test case review awaiting Test Manager sign-off

## Source Documents

- `01-input/03-prd/国际版标准官网 V1.2.2-银行卡优先购C端优化.zip` - original PRD package.
- `01-input/03-prd/extracted/国际版标准官网 V1.2.2-银行卡优先购C端优化.md` - extracted PRD markdown used for analysis.
- `01-input/03-prd/extracted/图片和附件/优先购C端流程交互原型V1.html` - comprehensive C-end interaction prototype.
- `01-input/03-prd/extracted/图片和附件/bank-card-presale-visa-only-demo-v1.html` - single bank-card priority-purchase prototype.
- `01-input/01-figma/figma.txt` - UI-kit Figma reference.
- `01-input/02-mindmap/` - empty as of 2026-07-15.

## Prior-Version Reference

- `../2026-06-25` - previous bank-card priority-purchase package.
- Prior signed consolidation: `../2026-06-25/02-analysis/requirement-consolidation-bank-card-priority-purchase.md`.
- Prior test workbook: `../2026-06-25/03-test-design/test-cases-bank-card-priority-purchase.xlsx`.
- Prior workbook reference state checked on 2026-07-15:
  - 28 rows with `Test Case ID`.
  - 69 embedded images.
  - Duplicate IDs present: `SIT-TC-WEB-BPP-014`, `SIT-TC-WEB-BPP-017`.

## Classification

This package is treated as a **requirement change evaluated like a new
requirement**.

Reason:

- The 2026-07-14 PRD changes the customer-facing business flow from
  "personal-center identity binding then checkout benefit decision" to
  "project-detail policy display, account-state recognition, inline bank-card
  validation, qualification acquisition, ticket-entry gating, and payment-stage
  recheck".
- The previous 2026-06-25 package remains a required reference for scope,
  wording style, screenshots, and regression impact.
- Test cases must follow the changed 2026-07-14 business flow, not mechanically
  patch the old case list.
- Future regenerated workbooks must yellow-highlight changed cells or changed
  rows and document the reason in comments where supported.

## Change Summary

- Adds a complete C-end priority-booking policy area on the Website project
  detail page.
- Displays configured priority-booking policies by type: bank card, membership
  card, stored-value card, and member level.
- Defines account-state handling for unauthenticated users, guest/temporary
  users, and registered users.
- Adds per-bank-card-item `立即验证` behavior through an on-page bank-card
  validation modal; signed decision is C-end input of the first 8 digits.
- Adds guest/temporary-account handling when the user tries to validate a bank
  card while a guest unpaid order may exist.
- Adds `获取资格` handling for membership-card and stored-value-card priority
  booking.
- Clarifies that priority booking does not have independent inventory and does
  not guarantee ticket availability.
- Requires ticket-entry / transaction-front rechecks for priority eligibility,
  ticket qualification, inventory, and project purchase rules.
- Clarifies that bank-card pre-validation does not guarantee payment success;
  payment-stage bank-card conditions are checked again.
- Multilingual / fallback testing is not a dedicated matrix for this round per
  signed Test Manager decision.
- Changes cart behavior: priority-booking projects do not support adding to cart
  before public sale; signed decision is to hide the cart icon.
- Keeps `Partner Benefits` in active scope for project-page validation data sync,
  viewing, and unbinding.

## Affected Modules

- Primary: Discount and Member Benefits (`08-discount`).
- Related:
  - Ticketing - project detail page, event/session entry, seat-selection and
    admission-ticket purchase paths, inventory, purchase qualification.
  - Payment - CyberSource/payment-stage bank-card condition recheck and failure
    handling.
  - Login and Registration - unauthenticated login redirect and guest/temporary
    account exit flow.
  - Membership Card / Stored-value Card - `获取资格` jump behavior and current
    holding-status recognition.
  - Internationalization - simplified Chinese, traditional Chinese, and English
    display for priority-booking content.

## Workflow Status

| Stage | Status | Location | Notes |
|---|---|---|---|
| 01-input | ready | `01-input` | PRD zip extracted; Figma URL captured; no mindmap. |
| 02-analysis | signed-off | `02-analysis/requirement-consolidation-priority-booking-c-end-optimization.md` | Test Manager signed off Q-1..Q-10 on 2026-07-15. |
| 03-test-design | qa2-pass | `03-test-design` | 38 SIT cases generated from signed Q-1..Q-10 decisions; changed-behavior cells are yellow-highlighted in the xlsx; QA2 r1 passed. |
| 04-test-case-review | awaiting-signoff | `04-test-case-review` | Test Manager review package generated and awaiting sign-off. |
| 05-execution | blocked | `05-execution` | Blocked until Test Manager signs off the test-case review package. |
| 06-execution-review | pending | `06-execution-review` | Not started. |
| 07-release-feedback | pending | `07-release-feedback` | Not started. |

## Key Outputs

- `01-input/input-index.md`
- `01-input/CHANGE.md`
- `02-analysis/previous-version-impact-reference.md`
- `02-analysis/requirement-analysis-detail-priority-booking-c-end-optimization.md`
- `02-analysis/requirement-consolidation-priority-booking-c-end-optimization.md`
- `02-analysis/requirement-consolidation-priority-booking-c-end-optimization.docx`
- `03-test-design/test-cases-priority-booking-c-end-optimization.md`
- `03-test-design/test-cases-priority-booking-c-end-optimization.xlsx`
- `03-test-design/CHANGE.md`
- `03-test-design/.iterations/qa2-review-priority-booking-c-end-optimization-r1.md`
- `03-test-design/.iterations/translation-review-priority-booking-c-end-optimization-r1.md`
- `04-test-case-review/test-case-review-priority-booking-c-end-optimization.md`
- `04-test-case-review/test-case-review-priority-booking-c-end-optimization.docx`

## Signed Decisions

- Q-1: Treat 7/14 as a new requirement evaluation; use 6/25 cases/screenshots
  as references only.
- Q-2: Keep `Partner Benefits` in active scope for validation data sync, viewing, and
  unbinding.
- Q-3: C-end asks users to input the first 8 digits for bank-card validation.
- Q-4: Display validation validity period on C-end.
- Q-5: Hide the cart icon before public sale; do not use click interception as
  the main path.
- Q-6: Website tests only visible payment success/failure results; CyberSource
  detailed certification remains payment-side responsibility.
- Q-7: Do not test checkout-page "priority qualification used" display.
- Q-8: B-side changes are outside this Website C-end package.
- Q-9: Old `mid` conflict is regression reference only; no new matrix.
- Q-10: No dedicated multilingual / fallback test matrix this round.

## Notes

- The package follows the 2026-07-15 clarified rule: similar requirement changes
  are evaluated like new requirements, with previous cases/screenshots used as
  required reference inputs.
