# Test Case Review and Approval - Promo Code / Bank-card Offer Promotion

Format version: 2.1

| Item | Value |
|----|----|
| Project / Module | West Kowloon Website - Discount Module |
| Package | `08-discount/2026-07-07` |
| Test Case Set | `../03-test-design/test-cases-promo-code-bank-card-offer.{md,xlsx}` |
| Case Version | v4 |
| Case Count | 20 SIT cases |
| Requirement Scope | `../02-analysis/requirement-consolidation-promo-code-bank-card-offer.md` |
| QA2 Review | `../03-test-design/.iterations/test-case-review-promo-code-bank-card-offer-r2.md` - Pass |
| Final Status | Signed Off |

## 1. Test Manager Final Sign-off

Put the Test Manager name in the `Signature / Confirmation` row.

| Sign-off Field | Value |
|----|----|
| Role | Test Manager |
| Sign-off Date | 2026-07-07 |
| Signature / Confirmation | Wang Yifan Evan |
| Final Comments | Signed off for execution. No additional Test Manager comments after v4 update. |

## 2. QA Review Summary

| Review Item | Result | Notes |
|----|----|----|
| Requirement scope signed | Pass | Requirement consolidation is Signed Off. |
| QA2 review completed | Pass | r2 review passed after v3 fixed r1 Test Steps wording issue. |
| Workbook validation | Pass | v4 `.xlsx` follows the approved project workbook schema. |
| Blocking findings | 0 | No open blocking test-design finding after v4 update and Test Manager sign-off. |
| Execution readiness | Ready | Approved to move to `05-execution` when execution planning starts. |

## 3. Coverage Summary

| Area | Coverage |
|----|----|
| Promo-code entry and recognition | BCO-001 to BCO-006 |
| CyberSource Checkout success/failure | BCO-007 to BCO-012, BCO-018, BCO-019 |
| Ticket-only and coexistence smoke | BCO-013 to BCO-015 |
| Regression and old BPP isolation | BCO-016, BCO-017 |
| Traceability / evidence support | BCO-020 |

## 4. Review Trail and Version Record

| Round / Version | Reviewer / Source | Review Comment Summary | Affected Test Case(s) / Artifact | Version Change / Closure Evidence | Status |
|----|----|----|----|----|----|
| QA2 r1 | QA2 (AI) | Test Steps contained assertion-style wording. | BCO-001 to BCO-015, BCO-018, BCO-020 Test Steps | QA1 prepared v3 update. | Needs Revision |
| v3 update | QA1 (AI) | Rewrite required for executable-only Test Steps. | BCO-001 to BCO-015, BCO-018, BCO-020 Test Steps | Rewrote affected Test Steps only; scope, IDs, priority, and expected results unchanged; updated `03-test-design/CHANGE.md`; regenerated `test-cases-promo-code-bank-card-offer.xlsx`. | Fixed |
| QA2 r2 | QA2 (AI) | Signed scope coverage confirmed; no blocking findings remained. | v3 test-case set | Closure verified by `../03-test-design/.iterations/test-case-review-promo-code-bank-card-offer-r2.md`; no further test-design change required before human sign-off. | Closed |
| Test Manager review | Test Manager | Translate test cases to English; remove `**` bold markers from Test Steps; leave Test Data blank when no specific data is required. | All 20 test cases; Test Steps; Test Data for BCO-001 and BCO-016 | Comments captured from the reviewer-edited DOCX before v4 update. | Needs Revision |
| v4 update | QA1 (AI) | Apply Test Manager review comments to the test-case artifacts. | All 20 test cases; Test Steps; Test Data for BCO-001 and BCO-016 | Translated cases to English; removed Test Steps bold markers; cleared non-required Test Data; updated `03-test-design/CHANGE.md`; regenerated `test-cases-promo-code-bank-card-offer.xlsx`. | Fixed - Awaiting Re-review |
| Test Manager sign-off | Test Manager | No additional comments after v4 update. | v4 test-case set | Reviewer removed comments, entered sign-off date, and confirmed signature in the DOCX; no Word comment parts remain in the signed document. | Signed Off |

## 5. Conditions and Next Step

| Item | Value |
|----|----|
| Conditions for Sign-off | None |
| Open Review Comments | None |
| Next Folder / Phase | `05-execution` |
| Handoff Decision | Proceed |
