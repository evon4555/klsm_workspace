# Test Cases CHANGE Log - Promo Code / Bank-card Offer Promotion

## v2 - 2026-07-07 (current)

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
