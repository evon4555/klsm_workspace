# Discount and Member Benefits Module Index

Module purpose:

- Member benefits, partner-member identity (鍚堜綔鏂逛細鍛?, BIN library, priority-
  purchase configuration, and the related customer-facing flows (identity
  binding, checkout benefit decision, and the bank-card priority-purchase vs
  bank-card discount conflict).

Package convention:

- Use direct date packages under this module, for example `2026-06-25`.
- Do not create a nested change-wrapper folder for new work.
- If two independent same-day changes need separate tracking, use
  `yyyy-mm-dd-story-<id>-<short-topic>`.
- Keep `<date-package>\package.md` in every date package as the traceability entry point.

Timeline:

| Package | Type | Status | Source | Change summary | Next workflow step |
|---|---|---|---|---|---|
| `2026-06-25` | requirement-change | analysis (awaiting consolidation sign-off) | 浼氬憳绯荤粺 v2.1 PRD (ZenTao story-702) + Figma + Yuque doc | Introduces partner-member system + BIN library + priority-purchase configuration + customer-facing 鎴戠殑鏉冪泭韬唤 + checkout benefit decision; headline customer scenario is "Purchase first with Bank card" (閾惰鍗′紭鍏堣喘). | Test Manager to sign off `2026-06-25\02-analysis\requirement-consolidation-bank-card-priority-purchase.md` (answer Q-1..Q-6 + U-1..U-6); 03-test-design is blocked until sign-off. |
| `2026-07-07` | new-requirement | test-case-review-signed | 钀ラ攢浼樻儬绯荤粺 V2.4.4 PRD slice (ZenTao story-633), chapter 2 bank-card offer promotion | Adds bank-card offer/coupon association for ticket promotion activities through CyberSource MID. Treated as same-module new requirement; `2026-06-25` BPP cases are impact reference only and must not be edited unless signed-off scope says so. | Test Manager signed off `04-test-case-review/test-case-review-promo-code-bank-card-offer.{md,docx}` on 2026-07-07 after v4 closure; ready for `05-execution` planning. |
| `2026-07-14` | requirement-change-as-new-evaluation | test-case-review-awaiting-signoff | International Website V1.2.2 bank-card priority-purchase C-end optimization PRD + Figma UI-kit reference + prior `2026-06-25` BPP cases/screenshots | Requirement consolidation signed off on 2026-07-15. Generated 38 SIT cases from final scope: project-detail priority-booking policy display, account-state recognition, first-8-digit bank-card validation with validity display, Partner Benefits sync/view/unbind path, qualification acquisition, ticket-entry gating, hidden cart icon before public sale, Website-visible payment recheck result, no checkout priority-used message, no dedicated multilingual fallback matrix. Prior cases/screenshots are required references; changed-behavior cells are yellow-highlighted in the xlsx. QA2 r1 passed; v1.1 terminology update changed `我的权益信息` / `我的权益身份` translation to `Partner Benefits`. | Test Manager to sign off `2026-07-14\04-test-case-review\test-case-review-priority-booking-c-end-optimization.docx`; `05-execution` is blocked until sign-off. |

Maintenance rule:

- Update this timeline whenever a date package is added or its workflow status
  changes.
- Use each package's `<date-package>\package.md` for source, affected modules, outputs, and
  open questions.
- Same-module new requirements should be isolated in their own date package.
  Previous same-module test cases are read-only impact references unless the
  signed consolidation explicitly instructs a versioned update.


