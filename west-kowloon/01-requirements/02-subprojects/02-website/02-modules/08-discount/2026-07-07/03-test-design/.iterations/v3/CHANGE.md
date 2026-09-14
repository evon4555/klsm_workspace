# Test Cases CHANGE Log - Promo Code / Bank-card Offer Promotion

## v3 - 2026-07-07 (current)

**Source dependency**:
- QA2 r1 review: `.iterations/test-case-review-promo-code-bank-card-offer-r1.md`

**Trigger**:
- QA2 r1 finding: Test Steps used assertion verbs (`检查`, `观察`, `查看`, `核对`, `确认`) instead of executable-only actions.

**Changes**:
- Modified Test Steps only for BCO-001, BCO-002, BCO-003, BCO-004, BCO-005, BCO-006, BCO-007, BCO-008, BCO-009, BCO-010, BCO-011, BCO-012, BCO-013, BCO-014, BCO-015, BCO-018, and BCO-020.
- No new cases added, no cases removed, no case IDs changed.
- Requirement scope, expected results, priorities, and old `2026-06-25` package isolation remain unchanged.
- Regenerated xlsx from the project template and marked 17 changed Test Steps cells with bright yellow (`FFFF00`) against v2.

**Yellow cells**:
- `FFFF00`: 17 changed cells.
- `FFFFF2CC`: 0 deferred cells.

**Previous-version snapshot**:
- `.iterations/v2/`

**Review status**:
- QA2 r2 review Pass: `.iterations/test-case-review-promo-code-bank-card-offer-r2.md`.
- Ready for Test Manager human sign-off in `04-test-case-review/`; no AI verdict has been placed in `04/`.

## v2 - 2026-07-07

**Reason**:
- Template correction after review feedback.

**Changes**:
- Aligned `test-cases-promo-code-bank-card-offer.md` with the project Excel template by adding the leading `Label` column.
- Regenerated `test-cases-promo-code-bank-card-offer.xlsx` by cloning `D:\Workspace\west-kowloon\01-requirements\01-source-documents\02-templates\TestCase_Template.xlsx`.
- Preserved the 20 signed-off case IDs, scenarios, scope, and old `2026-06-25` package isolation.
- Cleared design-time execution fields according to the template sample row.

**Review status**:
- Pending 04 test-case review.

## v1 - 2026-07-07

**Source basis**:
- Signed consolidation: `../02-analysis/requirement-consolidation-promo-code-bank-card-offer.md`
- PRD slice: `../01-input/03-prd/prd-markdown_Charpter2.txt`

**Scope decision**:
- This is a same-module new requirement under `08-discount/2026-07-07`.
- It does not modify `2026-06-25` bank-card priority-purchase test cases.
- Payment gateway, CyberSource MID, and card matching are treated as prepared test data / third-party payment behavior.

**This version contains**:
- 20 SIT cases covering promo-code entry, discount calculation before Checkout, CyberSource success/failure returns, ticket-only scope, light coexistence smoke, and isolation regression.
- 0 Deferred rows.

**Artifacts**:
- `test-cases-promo-code-bank-card-offer.md`
- `test-cases-promo-code-bank-card-offer.xlsx`

**Review status**:
- Pending 04 test-case review.
