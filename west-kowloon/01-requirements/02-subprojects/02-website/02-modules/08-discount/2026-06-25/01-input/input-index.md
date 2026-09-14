# Input Index

## Requirement Package

- Project: West Kowloon Website
- Primary module: Discount and Member Benefits
- Related modules: Ticketing, Payment, Login and Registration, Membership Card
- Package: `2026-06-25`
- Canonical location:
  `D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\08-discount\2026-06-25`

This package covers the 浼氬憳绯荤粺 v2.1 partner-member identity system + BIN
library + priority-purchase configuration + customer-facing 鎴戠殑鏉冪泭韬唤 +
checkout benefit decision. The headline customer-facing scenario is **"Purchase
first with Bank card" (閾惰鍗′紭鍏堣喘)**.

## Source Files

### PRD

PRD markdown is the working source for this package; the rendered Yuque doc
needs authenticated access.

- `03-prd\prd-markdown.txt` 鈥?full PRD text (浼氬憳绯荤粺 v2.1, created 2026-05-28
  by 闃晱鎱? revised 2026-06-11 to add multilingual support).
- `03-prd\yuque url.txt` 鈥?ZenTao story link
  `lengliwh.chandao.net/execution-story-702.html` plus the Yuque share-token
  URL (HTTP 401 from WebFetch on 2026-06-25; needs a logged-in browser).

### Figma

- `01-figma\figma.txt` 鈥?Figma frame
  `浼氬憳绯荤粺v2.0-浼氬憳绯荤粺` node `2548-14605`.
- `01-figma\reference link of UI.txt` 鈥?claude.ai public artifact referenced
  in the PRD as an interaction prototype.

### Mindmap

- `02-mindmap\` 鈥?folder exists but is empty as of 2026-06-25. If a mindmap
  branch is captured for this story later, add narrow PNGs here per
  `[[project-context: Mindmap Storage Convention]]`.

## Test Design Outputs

To be authored under `..\03-test-design` once analysis is complete. Use
numbered subfolders if multiple sub-scopes are needed (e.g.
`01-partner-member-admin`, `02-bin-library-admin`, `03-priority-purchase-config`,
`04-my-benefit-identity`, `05-checkout-benefit-decision`); decide during the
test-design step after the module-rename / admin-placement open questions in
`..\package.md` are resolved.

## Scope Notes

- Per source-authority rule (mindmap > PRD), PRD is currently the only source
  in this package (no mindmap branch yet). Treat PRD as the authoritative
  source for this package until a mindmap is added.
- 鐧藉悕鍗?and OAuth validation methods are documented in the PRD but **not in
  this release**; treat them as out-of-scope (no test cases) unless the user
  re-classifies them as Deferred.
- 浼氬憳涓撲韩椤圭洰 / 浼氬憳涓撲韩鍟嗗搧 / 淇冮攢娲诲姩 are out-of-scope this release; only
  浼樺厛璐?is in scope on the benefit-module side.
- Bank-card priority-purchase vs bank-card discount conflict rule (mid match
  vs mismatch) is in scope and must be tested in the customer-facing
  checkout flow.

## Website-Level Background

Rolling full-website PRD source documents and Figma references live under:

```text
..\..\..\..\..\01-source-documents\02-prd
..\..\..\..\..\01-source-documents\03-Figma
```

Those are background. This package's working inputs are the files listed
above.

