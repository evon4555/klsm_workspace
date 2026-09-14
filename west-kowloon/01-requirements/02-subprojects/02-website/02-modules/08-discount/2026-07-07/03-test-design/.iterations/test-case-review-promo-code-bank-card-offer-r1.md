# Test Case Review - Promo Code / Bank-card Offer Promotion

---

## [SECTION] Review Summary

- Review target: `../test-cases-promo-code-bank-card-offer.md` + `.xlsx` v2
- Requirement / feature: promo-code bank-card offer before CyberSource Checkout
- Reviewer role: QA2 (AI)
- Review date: 2026-07-07
- Overall result: Needs Revision
- Main concern: Several Test Steps cells contain assertion verbs such as `检查`, `观察`, `查看`, `核对`, or `确认`; per the harness wording rule, Steps should describe executable actions and assertions should live in Expected Result.

---

## [SECTION] Coverage Review

| Coverage Area | Status | Finding | Required Action |
|---|---|---|---|
| Main flow | Covered | Promo-code entry, validation, discount calculation, Checkout launch, and CyberSource success are covered by BCO-001, BCO-002, BCO-007, BCO-008, and BCO-018. | None. |
| Alternative flow | Covered | Delete/re-enter promo code, non-CyberSource path handling, coexistence smoke, and retry after payment failure are covered. | None. |
| Negative scenario | Covered | Invalid promo code, inapplicable promo code, MID mismatch, cancel/timeout, and missing gateway setup are covered. | None. |
| Boundary value | Partial / Accepted | The signed scope does not require promo-code length/format boundary enumeration; chapter 1 is background only. | No new case required for this package. |
| Permission | N/A | Customer-visible website flow only; admin/Pay Admin/SSO configuration is signed off as prepared test data or handled elsewhere. | None. |
| Data state | Covered | Order amount, applied promo state, payment status, and traceability are covered. | None. |
| Integration | Covered | CyberSource success/failure, MID mismatch, and gateway-data dependency are covered. | None. |
| Regression | Covered | Normal purchase without promo code and old BPP isolation smoke are covered by BCO-016 and BCO-017. | None. |

---

## [SECTION] Findings

| Severity | Issue | Impact | Suggested Fix |
|---|---|---|---|
| Major | BCO-001, BCO-002, BCO-003, BCO-004, BCO-005, BCO-006, BCO-007, BCO-008, BCO-009, BCO-010, BCO-011, BCO-012, BCO-013, BCO-014, BCO-015, BCO-018, and BCO-020 include assertion-style wording in Test Steps, such as `检查`, `观察`, `确认`, `查看`, or `核对`. | Execution is less clear because pass/fail checks are mixed into action steps; this weakens repeatability and violates the review-test-case Test Steps wording rule. | Rewrite only the affected Test Steps fields into actions such as `定位到`, `等待`, `打开`, `记录`, or `点击`; keep the observable checks in Expected Result. Do not change scope, IDs, priorities, or expected results. |

---

## [SECTION] Recommended Additions

| Suggested Case | Reason | Priority |
|---|---|---|
| None | Current signed scope is covered; no new case is required for r1. | N/A |

---

## [SECTION] Final Decision

- Decision: Needs Revision
- Required changes: Apply the Steps wording fix listed above, regenerate the xlsx from the project template, and run QA2 r2 review.
- Reviewer notes: This review is an AI review artifact and belongs in `03-test-design/.iterations/`; it must not be treated as Test Manager sign-off.
