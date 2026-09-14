# Website Mindmap Source

---

## [SECTION] Source Of Truth

- Feishu document: https://wtvrhpmlkj.feishu.cn/sheets/ClREs8Vd5hlcN8tbCMVco9yZnie?sheet=5BGvsg
- Format: Feishu spreadsheet used as mind map
- Access: requires Feishu login; edit/view permission pending as of 2026-05-15

The Feishu document is the live source of truth. The PNG snapshots in this folder are offline references only and may become stale.

---

## [SECTION] Scope

The mindmap covers the entire West Kowloon Website workstream, not a single requirement. Branches include but are not limited to:

- registration and login
- ticket purchase
- shopping cart and pricing
- payment
- e-ticket wallet
- account management
- content and event browsing
- multilingual user experience

Because the scope is broader than any single requirement package, this mindmap lives at the Website workstream level rather than under `02-modules\<module>\<yyyy-mm-dd>\01-input\`.

Each requirement package should reference the relevant branch of this mindmap rather than copy it.

---

## [SECTION] Local Snapshots

| File | Resolution | Captured | Notes |
|---|---|---|---|
| `website-mindmap-v0-whiteboard-export.png` | 1711 x 19378 | 2026-05-14 | Earlier whiteboard export. |
| `website-mindmap-v0-high-res.png` | 1653 x 20061 | 2026-05-15 | Higher resolution re-export. Both unreadable by image OCR due to aspect ratio. |

Image OCR fails on these snapshots because display scaling compresses each text row to 1-2 pixels.

Feishu does not export to OPML, Markdown, or CSV. The available export formats are PDF and Word (.docx). For text extraction with structure preserved, use DOCX. Cropped screenshots at a readable zoom level (e.g. one branch per image) also work for AI-side reading.

---

## [SECTION] Extraction Plan

Once Feishu access is granted:

1. Export the mindmap from Feishu as DOCX (preserves heading hierarchy best).
2. Save the file under this folder, e.g. `website-mindmap-v0.docx`.
3. AI converts the DOCX into a structured Markdown extract at `website-mindmap-extract.md`.
4. For each requirement package, add a `mindmap-scope.md` under `02-modules\<module>\<yyyy-mm-dd>\01-input\` pointing to the relevant branch of the extract.
5. Re-run `review-requirement-risk` for the current dry-run with the mindmap content included, and compare against the existing risk review to identify gaps.

If Feishu DOCX export is not feasible, cropped screenshots (one main branch per image, at readable zoom) are an acceptable fallback.

---

## [SECTION] Version

- Captured: 2026-05
- Live source: Feishu document above
- Treat PNGs as snapshots, not source of truth
