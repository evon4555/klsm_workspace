# Package 2026-06-25

Module: Discount and Member Benefits

Package date: 2026-06-25

Package type: requirement-change

Current status: analysis (awaiting consolidation sign-off)

## Source Documents

- `01-input/03-prd/prd-markdown.txt` — 会员系统 v2.1 PRD (created 2026-05-28 by 阮敏慧, rev 1.1 2026-06-11; multilingual support added in 1.1).
- `01-input/03-prd/yuque url.txt` — ZenTao story link `lengliwh.chandao.net/execution-story-702.html` + Yuque source doc (login required; share-token URL captured but returned 401 from WebFetch on 2026-06-25).
- `01-input/01-figma/figma.txt` — `会员系统v2.0-会员系统` Figma frame `node-id=2548-14605`.
- `01-input/01-figma/reference link of UI.txt` — claude.ai artifact reference for an interaction prototype.
- `01-input/02-mindmap/` — empty as of 2026-06-25; mindmap may be added later.

Headline customer-facing scenario: **"Purchase first with Bank card" (银行卡优先购)**.

## Change Summary

- Generalizes the existing 优先购合作方 capability into a full **partner-member identity system** (合作方会员管理), aligned with the existing internal-member model.
- Adds a centralized **BIN library** (BIN 库管理) decoupled from any single partner, reusable across partner-member levels.
- Introduces four partner validation methods (BIN / 白名单 / OAuth / API); this release lands only **BIN 校验** and **API 接口**. 白名单 and OAuth are documented but out of scope.
- Adds **合作方会员等级** support inside each benefit module's "限定会员等级" config, in parallel with internal-member levels.
- This release's benefit-side scope is narrowed to **优先购 (priority purchase)** only; 会员专享项目 / 会员专享商品 / 促销 are excluded.
- Customer-facing: new `我的权益身份` page in 个人中心 lets users proactively bind partner identities ahead of purchase; checkout-time benefit decision is automatic, **non-blocking**, and takes the best benefit when multiple rules match.
- Defines the **bank-card priority-purchase vs bank-card discount** conflict rule (mid match → both allowed; mid mismatch → discount disabled).
- Card-organization auto-recognition follows ISO/IEC 7812 prefix rules (Visa / Mastercard / 银联 / JCB / AmEx / Diners / Discover).
- Multilingual: 合作方名称, 备注, 等级名称.

## Affected Modules

- Primary: Discount and Member Benefits (this module).
- Related:
  - Ticketing — bank-card priority-purchase is exercised during ticket purchase, and the priority window plus benefit-decision logic affects checkout.
  - Payment — partner level binds 支付网关 + 商户支付号; the benefit-conflict rule references the order's `mid` from payment.
  - Login and Registration — 我的权益身份 lives inside 个人中心, requires authenticated user.
  - Membership Card — partner-member levels live alongside internal-member levels; cross-impact on member identity model.

## Workflow Status

| Stage | Status | Location | Notes |
|---|---|---|---|
| 01-input | partial | `01-input` | PRD markdown + Figma URL + Yuque URL captured; mindmap folder empty; user may add more. |
| 02-analysis | draft | `02-analysis/requirement-consolidation-bank-card-priority-purchase.md` | Consolidation doc drafted 2026-06-26 (first instance of harness Step 3.5 gate). Awaiting Test Manager sign-off on Q-1..Q-6 + U-1..U-6. |
| 03-test-design | blocked | `03-test-design` | Blocked by Step 3.5 gate — cannot start until consolidation doc reaches Signed Off. |
| 04-test-case-review | pending | `04-test-case-review` | — |
| 05-execution | pending | `05-execution` | — |
| 06-execution-review | pending | `06-execution-review` | Not started. |
| 07-release-feedback | pending | `07-release-feedback` | Not started. |

## Key Outputs

- _none yet_

## Open Questions

- **Module name vs scope**: folder slug `08-discount` is narrower than the actual 会员系统 v2.1 scope (partner-member identity + BIN + priority-purchase + checkout benefit logic). Consider renaming to `08-member-benefits` (or similar). Owner: 王一凡. Next action: confirm rename before risk-review writeup.
- **Admin-side placement**: 合作方会员管理 (§1.1), BIN 库管理 (§1.2), and 优先购配置 (§2.1) are operator/admin pages, not website-facing. They are currently parked under `02-website/02-modules/` together with the user-facing 我的权益身份 / 下单权益判定. Decide whether these belong here, in a separate backend/admin subproject, or split into two sibling packages. Owner: 王一凡.
- **Yuque source pull**: PRD text is available as markdown in `01-input/03-prd/prd-markdown.txt`, but the rendered Yuque doc (with images and possibly newer edits) needs an authenticated session. WebFetch with the share-token URL returned HTTP 401. Owner: 王一凡 / Claude (re-attempt with browser-side fetch if needed).
- **Out-of-scope methods**: 白名单 and OAuth validation paths are PRD-documented but not in this release — confirm they should be **omitted** rather than written as Deferred cases.
- **Benefit modules excluded this release**: 会员专享项目 / 会员专享商品 / 促销活动 are mentioned by PRD but excluded — confirm same.
- **HK-specific test data**: BIN samples need to include HK-issued cards (HSBC etc.) per `[[project_west_kowloon_hk_specific_features]]`; mainland team may need Deferred — HK-side verification flags for live card tests.

## Notes

- This is the first dated package under `08-discount`; module index timeline starts here.
- Source-authority order for West Kowloon (mindmap > PRD > Figma) still applies, but no mindmap exists for this story yet — PRD is currently the authoritative source until the mindmap branch is created.
