# Previous-Version Impact Reference

Package: `02-modules/08-discount/2026-07-14`

Reference package: `02-modules/08-discount/2026-06-25`

## Reference Artifacts Checked

| Artifact | Location | Reference Use |
|---|---|---|
| Prior requirement consolidation | `../2026-06-25/02-analysis/requirement-consolidation-bank-card-priority-purchase.md` | Signed scope, old C-end flow, resolved Q/U decisions. |
| Prior test-case workbook | `../2026-06-25/03-test-design/test-cases-bank-card-priority-purchase.xlsx` | Case style, prior screenshots/images, scenario coverage baseline. |
| Prior markdown cases | `../2026-06-25/03-test-design/test-cases-bank-card-priority-purchase.md` | Human-readable case list reference; note that it does not fully match workbook row count. |
| Prior package metadata | `../2026-06-25/package.md` | Historical source and affected-module summary. |

## Prior Workbook State

- Rows with `Test Case ID`: 28.
- Embedded images: 69.
- Duplicate IDs found: `SIT-TC-WEB-BPP-014`, `SIT-TC-WEB-BPP-017`.
- Missing/skipped ID sequence observed in workbook: `BPP-015`, `BPP-019`, `BPP-029` are not present in the actual xlsx row list checked on 2026-07-15.

These are reference-quality notes only. Do not carry duplicate IDs into the new
7/14 workbook.

## Old Flow Areas To Reuse As Reference

| Old Area | Old Case IDs / Evidence | New 7/14 Treatment |
|---|---|---|
| Personal-center identity page `Partner Benefits` | BPP-001..BPP-012 | Signed Q-2 keeps this in 7/14 scope for project-page validation data sync, viewing, and unbinding. Do not mechanically reopen the old 6/25 case list. |
| Bank-card BIN binding / validation | BPP-005..BPP-010 | Reuse validation wording style and image references, but redesign as project-detail on-page first-8-digit validation modal with validity-period display. |
| Checkout priority decision | BPP-013..BPP-016 | Redesign around project detail priority policy status, purchase-entry gating, and transaction-front recheck. |
| Quota / refund behavior | BPP-017..BPP-021 | Not explicit in 7/14 PRD. Keep as regression/open-question reference rather than default new scope. |
| i18n rendering | BPP-022..BPP-024 | Signed Q-10 says no dedicated multilingual / fallback matrix this round. Keep as reference only. |
| Cart / checkout E2E | BPP-026..BPP-028 | Must be revised because signed Q-5 says priority-booking projects do not support cart before public sale and should hide the cart icon. |

## 7/14 Changed Business Flow

The new authoritative flow is:

1. User enters the Website project detail page.
2. System loads public-sale status and configured priority-booking policies.
3. If no priority booking is configured, only normal public-sale entry is shown.
4. If priority booking is configured, the priority-booking policy area is shown.
5. Account state is recognized as unauthenticated, guest/temporary, or registered.
6. Policies are displayed by type: bank card, membership card, stored-value card, member level.
7. Registered users get status recognition and sorting; unauthenticated and guest users see full policy as not matched.
8. Bank-card items support per-item `立即验证` through a first-8-digit validation modal, and C-end displays validation validity period.
9. Membership-card and stored-value-card items support `获取资格`.
10. Purchase entry still rechecks priority eligibility, purchase qualification, inventory, and project rules.
11. Bank-card priority purchase still requires payment-stage bank-card condition recheck, but Website coverage is limited to visible success/failure results.
12. `Partner Benefits` remains in scope for validation data sync, viewing, and unbinding.

## Yellow Highlight Rule For Future Workbook

- Cells whose meaning changes from the 2026-06-25 reference must be filled yellow in the regenerated workbook.
- If an entire row replaces an old business-flow assertion, mark the changed cells or the row's ID cell yellow and add a comment explaining the reason.
- Purely new 7/14 rows that do not replace an old assertion are tracked as added cases; highlight is not required unless the row explicitly changes prior behavior.
- Do not reuse yellow for warnings or optional notes.
