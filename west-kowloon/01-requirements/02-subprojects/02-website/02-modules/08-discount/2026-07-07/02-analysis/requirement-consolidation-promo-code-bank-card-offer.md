# Requirement Consolidation — Promo Code / Bank-Card Offer Promotion

| Package | `02-modules/08-discount/2026-07-07` |
|---|---|
| Scope | `promo-code-bank-card-offer` |
| Author (AI) | QA1 |
| Reviewer (human) | Test Manager |
| Status | **Signed Off** |
| Classification | Same-module **new requirement**; do not mutate `2026-06-25` test cases unless Q-4 is changed by reviewer. |
| Sign-off rule | Test Manager answers Q/U items and changes the final revision-history row from Awaiting Sign-Off to Signed Off. AI never signs off its own scope. |

---

## 1. Source Inventory

| Source | Type | Location | Authoritative? | Notes |
|---|---|---|---|---|
| Marketing Discount System V2.4.4 PRD slice | PRD | `01-input/03-prd/prd-markdown_Charpter2.txt` | Yes, working source | No mindmap exists for this package. PRD first line says the new requirement starts from chapter 2: "促销活动支持银行优惠券活动". |
| ZenTao story-633 | Work item | Embedded in PRD: `lengliwh.chandao.net/execution-story-633.html` | Reference | Login required; not fetched in this pass. |
| Figma marketing discount system | UI reference | Embedded in PRD URL | Reference | Not fetched through Figma MCP. Use only as a pointer until screenshots/context are captured. |
| `08-discount/2026-06-25` | Prior same-module package | `../2026-06-25` | Reference only | Covers bank-card priority purchase / partner-member identity. It is not the source for this package. |

Source authority: West Kowloon's project rule is mindmap > PRD > Figma. Because no mindmap exists here, the PRD slice is the working authority.

---

## 2. Integrated Breakdown

### F1. Chapter-2 bank-card offer requirement boundary

- **Trigger:** this package is opened from PRD V2.4.4 with the note "new requirement starts from chapter 2".
- **Actor:** Test Manager / QA.
- **Expected behavior:** chapter 2 "促销活动支持银行优惠券活动" becomes this package's default test-design scope; chapter 1 promo-code behavior is treated as context unless Q-3 changes this.
- **Source:** PRD first line and chapter headers.
- **Related capabilities:** F2-F8.

### F2. CyberSource activity is configured in Pay Admin with MID

- **Trigger:** a bank-card promotion needs to be supported through CyberSource.
- **Actor:** Pay Admin operator / system integrator.
- **Expected behavior:** CyberSource activity exists in Pay Admin; merchant identifier is customized and uses MID.
- **Source:** PRD chapter 2, "第一步，在pay admin中配置cyberSource的活动...商户号使用MID".
- **Related capabilities:** F4, F6.

### F3. Promotion activity exposes "银行卡优惠" advanced action

- **Trigger:** operator opens the promotion activity list and the activity can be associated with a bank-card offer.
- **Actor:** Promotion admin operator.
- **Expected behavior:** the list advanced actions include "银行卡优惠"; clicking opens a modal for association.
- **Source:** PRD chapter 2, "在列表高级中，增加：银行卡优惠。点击在弹框中完成关联配置".
- **Related capabilities:** F4.

### F4. Promotion associates with CyberSource MID

- **Trigger:** operator configures bank-card offer association for a promotion activity.
- **Actor:** Promotion admin operator.
- **Expected behavior:** payment system is CyberSource only and default selected; operator selects the corresponding MID as the associated promotion merchant number.
- **Source:** PRD chapter 2, "目前支付系统仅支持cyberSource一种，默认选中；选择对应的商户号（MID）作为关联促销".
- **Related capabilities:** F2, F6, F7.

### F5. SSO enterprise parameter defines promotion-limited payment merchant numbers

- **Trigger:** enterprise/payment settings need to support promotion-limited merchant numbers.
- **Actor:** SSO / enterprise admin.
- **Expected behavior:** enterprise management parameter "促销活动限定支付方式商户号" is configured.
- **Source:** PRD chapter 2, "sso中配置支付网关：第一步，在企业管理的参数中配置：促销活动限定支付方式商户号".
- **Related capabilities:** F6, F7.

### F6. Payment gateway maps the corresponding merchant number

- **Trigger:** payment gateway setup is completed for the merchant number.
- **Actor:** Payment admin / payment configuration owner.
- **Expected behavior:** the payment gateway has the corresponding MID configured for CyberSource.
- **Source:** PRD chapter 2, "第二步，在支付网关中配置对应的商户号".
- **Related capabilities:** F2, F4, F7.

### F7. Checkout/payment determines bank-card offer eligibility by MID

- **Trigger:** customer reaches order confirmation or payment selection for a ticket order where bank-card promotion may apply.
- **Actor:** customer / checkout system.
- **Expected behavior:** the system can determine whether the current order/payment path matches the configured CyberSource MID and therefore whether the bank-card offer is available or applied.
- **Source:** inferred from PRD background "支持银行卡对接活动，需要配置促销信息与银行卡的mid" and chapter-2 configuration flow.
- **Related capabilities:** F4, F6, F8, F9.
- **Needs confirmation:** PRD text does not specify whether eligibility is checked at order confirmation, payment method selection, or payment callback.

### F8. No-match or missing-MID handling

- **Trigger:** no CyberSource MID is configured, the selected payment MID does not match the promotion MID, or the gateway setup is incomplete.
- **Actor:** customer / checkout system / admin.
- **Expected behavior:** the bank-card offer should not be applied; exact UI/admin error behavior is not specified.
- **Source:** negative path inferred from F4-F7.
- **Related capabilities:** F7.

### F9. Coexistence with existing promotion and benefit rules

- **Trigger:** a bank-card offer appears together with normal promotion, promo code promotion, member-card promotion, or the prior bank-card priority-purchase benefit.
- **Actor:** customer / pricing engine.
- **Expected behavior:** coexistence/conflict follows product rules; current PRD does not explicitly connect chapter 2 bank-card offer to the chapter 1 promo-code mutual-exclusion rules or to `2026-06-25` BPP rules.
- **Source:** PRD chapter 1 mutual-exclusion rules; `2026-06-25` BPP conflict rule; chapter 2 bank-card MID association.
- **Needs confirmation:** see Q-5 and U-7.

---

## 3. Differences

### 3.1 vs Previous Same-Module Package (`prev`)

| ID | Capability | Previous Behavior | New Behavior | Source |
|---|---|---|---|---|
| D-prev-1 | F7/F9 | `2026-06-25` covers bank-card priority purchase through partner-member identity and checkout benefit decision. | `2026-07-07` covers bank-card offer/coupon activity associated by CyberSource MID. | `../2026-06-25/package.md`; PRD V2.4.4 chapter 2 |
| D-prev-2 | F4/F7 | Prior package uses MID in the bank-card priority-purchase vs bank-card discount conflict rule. | New package uses MID as the association key between promotion and CyberSource merchant setup. | `../2026-06-25/02-analysis/...`; PRD chapter 2 |
| D-prev-3 | F1 | Prior package has no promo-code scope. | PRD includes chapter 1 promo-code rules, but the package note says the new requirement starts from chapter 2. | PRD first line and chapter 1 |

### 3.2 vs Standard Product (`std`)

| ID | Capability | Standard Product Behavior | This Project's Behavior | Sync Back? | Source |
|---|---|---|---|---|---|
| D-std-1 | F2-F4 | Standard marketing discount system can configure promotion activities. | West Kowloon requires CyberSource bank-card offer association through MID. | TBD | PRD background and chapter 2 |
| D-std-2 | F5-F6 | Payment gateway / enterprise parameters may be product-wide configuration. | West Kowloon requires "促销活动限定支付方式商户号" and corresponding CyberSource MID mapping. | TBD | PRD chapter 2 |

### 3.3 vs Adjacent Module (`adj`)

| ID | Capability | Adjacent Module Affected | Nature of Impact | Source |
|---|---|---|---|---|
| D-adj-1 | F7 | Ticketing / order confirmation | Checkout may need to surface, apply, or suppress a bank-card offer based on MID. | PRD chapter 2 |
| D-adj-2 | F2/F6 | Payment / CyberSource | Payment configuration must expose MID consistently to promotion eligibility. | PRD chapter 2 |
| D-adj-3 | F5 | SSO / enterprise management | Enterprise parameter controls which merchant numbers can be used for promotion-limited payment. | PRD chapter 2 |
| D-adj-4 | F9 | Membership card / promotion policy | Bank-card offer coexistence with member-card promotion, promo code, normal promotion, and BPP needs a clear rule. | PRD chapter 1 + `2026-06-25` |

---

## 4. Test Scope This Round

### 4.1 In Scope — proposed after sign-off

| Capability | Scope Statement | Rationale |
|---|---|---|
| F7 | Customer selects/enters the promotion code before Checkout, then proceeds to CyberSource; website-side test verifies final payment success/failure return. | Signed-off scope: CyberSource/MID/card validation is treated as third-party/payment test data, not website-side rule enumeration. |
| F8 | Negative payment-result paths for unmatched or incomplete MID/card/payment-gateway setup. | Prevents false assumptions that the website can pre-validate every third-party payment rule. |
| F9 | Isolation and smoke coexistence checks only; do not enumerate every combination of promo code, normal promotion, member-card promotion, and bank-card priority purchase. | Signed-off answer says backend config determines stackability and combinations can be tried later. |
| F3-F4 | Only prerequisite/test-data awareness, not full admin CRUD coverage. | Signed-off answer says payment gateway/admin setup should be prepared before test as test data. |

### 4.2 Out of Scope — deferred by default

| Capability | Reason Deferred | Target Package |
|---|---|---|
| Chapter 1 promo-code full behavior | PRD note says the new requirement starts from chapter 2. | TBD if Test Manager changes Q-3. |
| Shopping-cart / multi-event application flow | PRD says the promo-code shopping-cart wireframe is not needed this version; bank-card offer multi-event behavior is not specified. | TBD |
| Detailed visual validation against Figma | No Figma screenshot or MCP context captured in this pass. | Same package after Figma context is captured, if required. |

### 4.3 Out of Scope — handled elsewhere by default

| Capability | Owner | Pointer |
|---|---|---|
| Pay Admin CyberSource activity CRUD | Payment / Pay Admin test owner | PRD chapter 2 F2 |
| SSO enterprise parameter CRUD | SSO / enterprise management test owner | PRD chapter 2 F5 |
| Payment gateway merchant-number configuration CRUD | Payment gateway test owner | PRD chapter 2 F6 |
| Full promotion admin UI CRUD | Standard-product/admin test suite | PRD chapter 2 F3-F4 unless Q-2 says this package owns it |

---

## 5. Unclear Items

| ID | Source Location | Ambiguity | Working Assumption |
|---|---|---|---|
| U-1 | PRD first line + chapter 1 | The file contains chapter 1 promo-code rules, but the note says the new requirement starts from chapter 2. | Chapter 1 is context only. |
| U-2 | PRD background + chapter 2 | "银行卡" is mentioned, but the concrete association key is MID. The text does not say card BIN, issuer, or card organization participates in eligibility. | Website tests do not validate BIN/card issuer rules directly; use prepared CyberSource/payment-gateway test data and observe payment success/failure. |
| U-3 | PRD chapter 2 | The text does not state whether bank-card offer availability is evaluated at order confirmation, payment method selection, payment submit, or payment callback. | Evaluate through Checkout -> CyberSource -> return result. If MID/card/gateway configuration matches, payment succeeds; otherwise payment fails. |
| U-4 | PRD chapter 2 | Behavior when multiple promotion activities map to the same MID, or one promotion maps to multiple MIDs, is not specified. | One promotion maps to one selected MID; duplicate association is blocked or controlled by admin config. |
| U-5 | PRD chapter 2 | Missing or mismatched MID UI/error behavior is not specified. | Do not invent a website-side precheck message. Treat mismatch as payment failure/unsuccessful return unless product later defines UI copy. |
| U-6 | PRD chapter 1 shopping-cart note + chapter 2 | Multi-item shopping-cart behavior is explicitly "not needed" for promo code, but not explicitly scoped for bank-card offer. | This package covers immediate single ticket order first; shopping cart is deferred. |
| U-7 | PRD chapter 1 + prior package | The relationship between bank-card offer and `2026-06-25` bank-card priority-purchase conflict rules is not explicit. | Keep old BPP cases unchanged. This package stays isolated and covers only light coexistence smoke; full combination matrix can be added later. |
| U-8 | PRD images/Figma | Several flow/UI details are in images; text does not fully describe them, and Figma has not been fetched. | Proceed without Figma for first test design. Flow: select ticket -> select/enter promo code before Checkout -> Checkout -> CyberSource return success/fail. |

---

## 6. Items Requiring User Confirmation

| ID | Question | Options | Owner | Signed-off answer |
|---|---|---|---|---|
| Q-1 | Is `2026-07-07` a same-module new requirement package, not a change to `2026-06-25` test cases? | (a) Yes, keep isolated / (b) No, treat as change to old BPP package / (c) split into two packages | Test Manager | (a) Yes, keep isolated. |
| Q-2 | Who owns full admin-side configuration test cases for Pay Admin, SSO, payment gateway, and promotion backend? | (a) Standard/admin teams own full CRUD; this package owns only integration and customer-visible behavior / (b) this package owns full admin config cases too / (c) split separate admin package | Test Manager | Ignore that part; this payment gateway should be prepared before test as test data. |
| Q-3 | Should chapter 1 "促销活动支持促销码" be included in this package's test-design scope? | (a) No, context only / (b) include only overlap with bank-card offer / (c) include full promo-code cases | Test Manager / PM | Chapter 1 is reference to understand the background. The promo id/code still needs to be filled so it can be recognized on UI. |
| Q-4 | If a new bank-card offer rule conflicts with old `2026-06-25` BPP cases, how should we update? | (a) Do not change old cases now; add cross-regression here / (b) reopen old package with snapshot + CHANGE / (c) both | Test Manager | (a), unless product says old behavior is replaced. If it becomes old-function refactoring, check old test cases first to decide whether old cases need updates or new cases should cover the changes. Still generate new documents in the new timestamp folder. |
| Q-5 | What is the coexistence rule for bank-card offer with promo code, normal promotion, member-card promotion, and bank-card priority purchase? | (a) Follow existing mutual-exclusion switches and BPP MID rule / (b) bank-card offer is mutually exclusive with all other offers / (c) bank-card offer can stack with selected policies by config | PM / Test Manager | (c) Backend setup determines how many promotion ways can be used. Keep isolated first and try combinations later; do not enumerate each combination now. |
| Q-6 | When should bank-card offer eligibility be evaluated? | (a) order confirmation before payment / (b) payment-method selection when MID is known / (c) payment submit/callback / (d) multiple checkpoints | Dev / PM | Payment success or not. The website launches Checkout, then CyberSource checks whether the MID is configured with this card/payment gateway. If matched, payment succeeds; otherwise payment fails. |
| Q-7 | Is CyberSource the only payment-system path to cover this round? | (a) Yes, only CyberSource; other methods negative/not shown / (b) include future payment providers as deferred placeholders / (c) include generic payment abstraction cases | Test Manager | (a) Yes, only CyberSource. This is a third-party check; website testing only needs to care whether payment succeeds or not. |
| Q-8 | Should Figma be fetched before test-case design? | (a) No, PRD text is enough for first test design / (b) yes, fetch Figma before UI-specific cases / (c) only fetch if reviewer flags UI ambiguity | Test Manager | (b) Yes in principle, but not available now. This is only a place to add promo code and other promotion methods. Flow: select ticket -> before Checkout select/enter promo code to get discount -> click Checkout -> pay via CyberSource -> get success/fail return code. |

---

## 7. Hand-Off Statement

Scope is **Signed Off**: this is an isolated same-module new-requirement package. `03-test-design` should produce `test-cases-promo-code-bank-card-offer.md` and `.xlsx` under `2026-07-07` only. Old `2026-06-25` BPP test cases remain untouched; if product later confirms old behavior is replaced, reopen the old package through snapshot + `CHANGE.md` versioning.

---

## 8. Notes

- This document is the gate for `03-test-design/`.
- The date package is the boundary that protects previous test cases. Same module does not imply same test-case file.
- If sources change after sign-off, create a new revision of this consolidation doc and re-request sign-off before updating test cases.

---

## 9. Revision History

| Date | Author | Change | Status |
|---|---|---|---|
| 2026-07-07 | QA1 (AI) | First consolidation draft from `01-input/` and prior-package impact scan. | Done |
| 2026-07-07 | Test Manager | Signed off. Answers captured in Q-1..Q-8; U assumptions accepted with Q-driven adjustments. | **Signed Off** |

Sign-off rule: status moves to **Signed Off** only by the Test Manager. AI writes "Done" for its own rows, never "Signed Off".
