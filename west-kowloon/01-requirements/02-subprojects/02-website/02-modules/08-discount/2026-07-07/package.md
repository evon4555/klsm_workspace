# Package 2026-07-07

Module: Discount and Member Benefits

Package date: 2026-07-07

Package type: new-requirement

Current status: test-case-review-signed

## Source Documents

- `01-input/03-prd/prd-markdown_Charpter2.txt` - Marketing Discount System V2.4.4 PRD slice, product owner 阮敏慧, created 2026-03-18, ZenTao story-633.
- Figma URL is embedded in the PRD slice but has not been fetched through Figma MCP in this analysis pass.
- `01-input/01-figma/` and `01-input/02-mindmap/` are present but empty as of 2026-07-07.
- Related prior package: `../2026-06-25` bank-card priority-purchase. It is used only as impact reference, not as a target for edits.

## Classification

This package is treated as a **same-module new requirement**, not an update to the existing `2026-06-25` test cases.

Reason:

- The source is a separate PRD/story thread: Marketing Discount System V2.4.4 / story-633.
- The PRD note says the new requirement starts from chapter 2: "促销活动支持银行优惠券活动".
- The prior `2026-06-25` package covers partner-member identity and bank-card priority purchase. This package covers bank-card offer/coupon association through CyberSource MID.
- No old `2026-06-25` test-case assertion is changed unless the Test Manager later confirms a direct behavioral replacement or conflict.

Working rule:

- New scenarios are written under this package after sign-off.
- Existing `2026-06-25` cases are not modified from this package.
- If sign-off confirms impact to old BPP cases, first snapshot the old version, then update through that package's `CHANGE.md` versioning process.

## Change Summary

- Adds bank-card offer/coupon association for ticket promotion activities.
- Requires CyberSource activity setup in Pay Admin with custom merchant identifier using MID.
- Adds "银行卡优惠" entry under the promotion activity list's advanced actions, opening a modal to associate a promotion with a MID.
- Current payment system support is CyberSource only, default selected.
- Adds SSO/enterprise parameter and payment-gateway MID configuration as prerequisite cross-system setup.
- Needs confirmation on the customer-facing checkout/payment behavior because the text PRD mostly describes configuration and references flow images.

## Affected Modules

- Primary: Discount and Member Benefits (`08-discount`).
- Related:
  - Ticketing / order confirmation: whether the bank-card offer is displayed or applied during checkout.
  - Payment: CyberSource and MID mapping determine eligibility.
  - SSO / Enterprise management: parameter configuration for promotion-limited payment merchant numbers.
  - Membership Card / Promotion policy: potential coexistence or conflict with member-card promotion, promo code, normal promotion, and prior bank-card priority-purchase rules.

## Workflow Status

| Stage | Status | Location | Notes |
|---|---|---|---|
| 01-input | partial | `01-input` | PRD slice exists. Figma and mindmap folders are empty. |
| 02-analysis | signed-off | `02-analysis/requirement-consolidation-promo-code-bank-card-offer.md` | Step 3.5 scope gate signed off 2026-07-07; Q-1..Q-8 answered and U assumptions accepted with adjustments. |
| 03-test-design | updated-v4 | `03-test-design` | 20 isolated SIT cases updated to v4 after Test Manager comments: English translation, plain Test Steps numbering, and blank Test Data where no specific data is required. Old `2026-06-25` cases were not changed. |
| 04-test-case-review | signed-off | `04-test-case-review/test-case-review-promo-code-bank-card-offer.md` + `.docx` | Test Manager signed off v4 on 2026-07-07 after comments were applied and removed; no open review comments remain. |
| 05-execution | ready | `05-execution` | Ready to start when execution planning begins. |
| 06-execution-review | pending | `06-execution-review` | Not started. |
| 07-release-feedback | pending | `07-release-feedback` | Not started. |

## Key Outputs

- `01-input/input-index.md`
- `02-analysis/requirement-consolidation-promo-code-bank-card-offer.md`
- `02-analysis/requirement-consolidation-promo-code-bank-card-offer.docx`
- `03-test-design/test-cases-promo-code-bank-card-offer.md`
- `03-test-design/test-cases-promo-code-bank-card-offer.xlsx`
- `03-test-design/CHANGE.md`
- `03-test-design/.iterations/test-case-review-promo-code-bank-card-offer-r1.md`
- `03-test-design/.iterations/test-case-review-promo-code-bank-card-offer-r2.md`
- `03-test-design/.iterations/test-case-review-promo-code-bank-card-offer-r1.docx`
- `03-test-design/.iterations/test-case-review-promo-code-bank-card-offer-r2.docx`
- `03-test-design/.iterations/iteration-log-promo-code-bank-card-offer.md`
- `04-test-case-review/test-case-review-promo-code-bank-card-offer.md`
- `04-test-case-review/test-case-review-promo-code-bank-card-offer.docx`

## Open Questions

- Confirm that this package should cover only chapter 2 "促销活动支持银行优惠券活动"; chapter 1 "促销活动支持促销码" is context unless explicitly pulled in.
- Confirm whether full admin-side configuration cases belong in this Website module package or in the standard-product/admin test suite.
- Confirm how this bank-card offer feature interacts with the prior `2026-06-25` bank-card priority-purchase vs bank-card discount conflict rule.
- Confirm whether customer-facing eligibility is determined only by MID or also by card BIN / card issuer / payment method.

## Notes

- This package exists to isolate the new requirement from previous cases in the same module.
- Folder naming is still useful: the date package is the first separation boundary. Use a story-suffixed package only when same-day same-module changes are independent enough to need separate ownership/status.
