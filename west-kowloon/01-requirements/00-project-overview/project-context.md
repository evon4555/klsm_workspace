# Project Context

---

## [SECTION] Source Baseline

Current project context is derived from:

- `D:\Workspace\west-kowloon\01-requirements\01-source-documents\01-it-pmo\IT-PMO-410-Requirement-Document_V1.0.pdf`
- `D:\Workspace\west-kowloon\01-requirements\01-source-documents\01-it-pmo\IT-PMO-420-Functional-Specification-Document_V1.0_0414.docx`
- `D:\Workspace\west-kowloon\01-requirements\01-source-documents\02-templates\TestCase_Template.xlsx`

This is a working project summary for QA planning and test design. Requirement-level details should still be analyzed in each requirement package.

---

## [SECTION] Project Identity

The project appears to be for the West Kowloon Cultural District Authority and concerns:

- Ticketing and Admission System
- ancillary B2C applications
- customer-facing website and related channels
- operational ticketing and admission capabilities

The functional specification targets a large venue and cultural district context with end-to-end ticketing, admission, and customer journey support.

---

## [SECTION] Business Scope

The project scope includes multiple operational and customer-facing areas:

- box office ticket sales
- reserved seating and general admission sales
- shopping cart and pricing flows
- discount and bundle handling
- payment processing
- ticket issuance and printing
- ticket exchange and collection
- website registration and login
- content and event browsing
- e-ticket wallet
- self-service kiosk flows
- OTA integration
- admission control and terminal operations
- reporting and operational management

---

## [SECTION] Website Scope

The Website is the customer-facing B2C channel within the broader West Kowloon ticketing and admission ecosystem.

The Website stream likely includes:

- registration and login
- content and event browsing
- ticket purchase
- payment
- e-ticket wallet
- account-related pages
- multilingual user interaction

Website requirement details should be captured under:

- `D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules`

---

## [SECTION] Architecture View

The project appears to include several connected domains rather than a single isolated website:

- customer-facing website and B2C journeys
- box office operations
- self-service ticketing and collection
- admission terminals and access control
- OTA and external integrations
- payment integrations
- backend ticketing and operational management
- reporting and data output

This architecture shape implies high cross-channel regression risk. Payment, inventory, ticket issuance, admission validation, permissions, and reporting consistency should be treated as important QA areas.

---

## [SECTION] Roles And Permissions

The current role model is inferred from the functional specification and should be treated as provisional until a formal permission matrix is available.

| Role | Description | Testing Focus |
|---|---|---|
| Customer / End User | Public or registered website user | registration, login, purchase, wallet, account, payment, language behavior |
| Box Office Staff | Staff operating onsite sales workflows | login, scope, ticket sales, changes, payment handling, restricted operations |
| Admission Staff | Staff validating or managing admission | terminal login, scope, admission validation, record visibility |
| Backend Operator / Admin | Staff managing ticketing and operational settings | permissions, sensitive actions, auditability |
| Integration / External Channel | OTA or partner system behavior | data consistency, status sync, return and validation flows |

Permission-sensitive areas include:

- login and authenticated access
- venue or scope-based staff access
- ticket exchange, refund, reprint, and reservation actions
- admission scope review and account switching
- backend reporting and configuration access
- customer access to owned tickets only

UI visibility alone is not enough; server-side authorization should be verified where possible.

---

## [SECTION] Environment Assumptions

A full environment matrix is not yet available from the current source set.

Known hints:

- The project test case template references `SIT / UAT / PROD`.
- The wider platform likely includes website, backend, payment integration, admission devices, kiosk, and box office related environments.

Until confirmed otherwise, assume testing may need:

- SIT for functional and integration validation
- UAT for business confirmation and release readiness
- PROD for controlled post-release validation only

Missing information to collect:

- environment URLs
- build and deployment identification rules
- account and role setup per environment
- test data preparation rules
- payment sandbox behavior
- OTA or external integration test endpoints
- device or terminal test environment mapping

---

## [SECTION] QA Implications

This project should be treated as business-critical because it likely affects:

- online ticket sales revenue
- ticket inventory and seat allocation accuracy
- admission correctness
- customer account and login behavior
- payment and post-payment fulfillment
- multilingual customer experience
- operational workflows used by venue staff

QA planning should prioritize:

- main purchase and admission flows
- role-based behavior
- inventory and locking logic
- payment result handling
- wallet visibility and ticket status after purchase
- multilingual correctness
- cross-channel regression protection
- evidence and traceability for release decisions

---

## [SECTION] Context Usage Rules

When generating QA outputs such as risk review, test strategy, or test cases, use context in this order:

1. Requirement layer
2. Project layer
3. Company layer

If there is a conflict:

- requirement-specific facts have highest priority
- project context should be updated later if repeated requirement work reveals missing or outdated project understanding
- company context should be treated as general background only

Do not force all new information into the project layer immediately. First confirm it through real requirement work, then decide whether it belongs in company context, project context, or requirement-only context.

---

## [SECTION] Source Authority

(Declared 2026-05-15. See `D:\Workspace\qa-harness\01-system\07-source-authority.md` for the system-level principle.)

| Source | Authority | Location |
|---|---|---|
| Mindmap | **Authoritative** | Live in Feishu. Master mindmap snapshots and structured extract under `02-subprojects/02-website/01-source-documents/01-mindmap/`. Per-change narrow captures under `02-subprojects/02-website/02-modules/<module>/<yyyy-mm-dd>/01-input/02-mindmap/`. |
| PRDs | Reference | Website-level PRDs (cover the whole Website) under `02-subprojects/02-website/01-source-documents/02-prd/`; change-scoped PRD slices, if any, under `02-subprojects/02-website/02-modules/<module>/<yyyy-mm-dd>/01-input/03-prd/`; project-wide PRDs / IT-PMO docs under `01-source-documents/01-it-pmo/`. |
| Figma | Reference / UI | Website-level UI references under `02-subprojects/02-website/01-source-documents/03-Figma/`; change-scoped UI inputs under `02-subprojects/02-website/02-modules/<module>/<yyyy-mm-dd>/01-input/01-figma/`. |
| IT-PMO documents | Reference / historical | `01-source-documents/01-it-pmo/`. |

Rules:

- **PRD-fills-gap**: items in PRD but absent from the mindmap are still in scope. Rationale: the mindmap author was reading the PRD, so absence is most likely oversight rather than deliberate exclusion.
- **Mindmap "PRD 上没写" annotation**: treat as deliberate scope confirmation; in scope.
- **Mindmap narrowing labels (e.g., "只支持邮箱")**: take the sub-tree content as truth; treat the label as guidance overriding any PRD wording it contradicts.

---

## [SECTION] Test Case Template

The project's test case template is **authoritative** for all test case deliverables (md and xlsx).

- **Template file**: `D:\Workspace\west-kowloon\01-requirements\01-source-documents\02-templates\TestCase_Template.xlsx`
- **Rule**: Follow it exactly. Do **not** add columns (no extra "Evidence Required", "Notes", etc.). Do **not** remove columns. Do **not** change column order. If a column seems missing, raise it with the user — do not silently invent one.
- **Apply to both formats**: the markdown table inside `test-cases-*.md` and the generated `test-cases-*.xlsx` must both use the same 20 columns in the template's order.

**20 columns (in order):**

1. Label (SIT/UAT/PROD/NA) - default `SIT` for SIT design cases
2. Test Case ID - e.g. `SIT-TC-WEB-AUTH-001`
3. Module/Feature
4. Priority (High/Medium/Low)
5. Severity (High/Medium/Low)
6. Collected from - source trace (requirement ID, mindmap branch, PRD section)
7. Test Scenario
8. Test Case Description
9. Preconditions (if any)
10. Test Steps  *(note: Steps before Data per template)*
11. Test Data (if any)
12. Expected Result
13. Test Case Owner - default `Antank QA Team` (template sample has this value, so it's the project default)
14. Environment (SIT/UAT/PROD) - **blank** at design time (template sample is empty here; the `(SIT/UAT/PROD)` in the header is a list of valid values, not a default to fill in)
15. Execution Date - blank at design time
16. Executed By - blank at design time
17. Actual Result - blank at design time
18. Status (Pass/Fail) - blank at design time
19. Comments/Remarks - blank at design time
20. Screenshots - blank at design time

**Rule for defaults**: a cell gets a default value only when the template's sample row has that value populated. If the sample row leaves the cell blank, leave it blank in generated cases — header tags in parentheses (`(SIT/UAT/PROD)`, `(Pass/Fail)`, etc.) describe valid values, not defaults.

**Content format follows the sample row's style.** Current sample patterns:
- `Test Steps`: numbered `1. xxx\n2. xxx`.
- `Expected Result`: numbered `1. xxx\n2. xxx` — one numbered point per observable expectation. Split clauses on `;` into separate points.

The sample row (`SIT-TC-AMW-017`, ticket purchase flow) is for tone / level-of-detail / format reference only, not scope.

**Mindmap-`?` items → light-yellow fill (`FFFFF2CC`)**: every `?` marker in the mindmap (open / to-confirm items) gets an **explicit Deferred test case** with the row filled `FFFFF2CC` light yellow. If an existing case already covers the surrounding behavior but one of its cells depends on the `?` item (e.g., an Expected Result that says "lands on TBD page"), fill just that cell yellow instead of duplicating the case. This makes mindmap-to-case coverage visually traceable: every `?` is either a yellow row (new Deferred case) or a yellow cell (existing case awaiting product confirmation).

**Coverage rule**: every leaf-level mindmap branch must map to at least one test case (or one yellow cell on an existing case). Sub-trees of pure attributes (e.g., 验证码邮件 → 格式 / 内容 / 发件人 / 标题) can be bundled into one case. Cross-cutting concerns (多语言, "以上所有错误,多语言") can be covered by one multilingual case + cross-cutting notes in other cases.

**Ticket type flow split rule**: for ticketing, cart, checkout, payment,
discount, refund, wallet, order detail, and related regression scopes, consider
`Admission ticket` (门票) and `seat-selection ticket` (座票) as separate flows.
Charisma/downstream handling can differ between these two paths, so one ticket
type must not be treated as implicit coverage for the other. Generate separate
cases whenever behavior, data, inventory/seat locking, pricing, payment,
discount eligibility, order detail, wallet, refund, or downstream handling can
differ. If a requirement is truly not applicable to one ticket type, record the
explicit `NA` rationale in Coverage Notes or review evidence.

---

## [SECTION] Translation Style

For Chinese-to-English translation of West Kowloon QA artifacts, use the style
approved in:

`D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\08-discount\2026-07-07\03-test-design\test-cases-promo-code-bank-card-offer.xlsx`

Use short, direct, professional QA English. Preserve identifiers, test data,
case IDs, F/Q/U references, filenames, system names, and payment terms exactly.
Do not add explanatory content that is not in the source. For test cases, keep
`Test Steps` as user actions and `Expected Result` as observable outcomes.
Use `translation-glossary.md` as the first terminology reference.

Use the project-owned skill
`D:\Workspace\west-kowloon\01-requirements\00-project-overview\project-ai-skills\westk-zh-en-translation\SKILL.md`
for future West Kowloon Chinese-to-English translation tasks. Codex user-local
skills are launchers only. After translated artifacts are produced, run the
harness `review-translation-quality` workflow before handoff.

---

## [SECTION] Project AI Skills

Portable project-owned AI workflow skills live under:

`D:\Workspace\west-kowloon\01-requirements\00-project-overview\project-ai-skills`

This folder is the source of truth for West Kowloon AI workflow routing across
Codex, Claude Code, and other tools. User-local folders such as
`C:\Users\klsm\.codex\skills` are launchers only and must point back to this
project folder.

Current project skills:

- `westk-testcase-workflow` - test case generation, QA2 review, revision,
  workbook regeneration, and ticket-type split routing.
- `westk-review-signoff` - review comments, formal DOCX rendering, Review
  Trail, and Test Manager sign-off sync.
- `westk-zh-en-translation` - Chinese-to-English translation style and
  translation quality review routing.

For Claude Code migration, start from `D:\Workspace\west-kowloon\CLAUDE.md`.
For Codex migration or a rarely used Codex session, start from
`D:\Workspace\west-kowloon\CODEX.md`.
For other agent migration, start from `D:\Workspace\west-kowloon\AGENTS.md`.

---

## [SECTION] Review Templates

The project keeps human-facing review template files beside the xlsx test case template:

| Template | Purpose |
|---|---|
| `D:\Workspace\west-kowloon\01-requirements\01-source-documents\02-templates\Requirement Review Template.docx` | Version 2.1 external-share-ready Test Manager requirement review / scope sign-off form for `02-analysis/requirement-consolidation-<scope>.md`. |
| `D:\Workspace\west-kowloon\01-requirements\01-source-documents\02-templates\Test Case Review Template.docx` | Version 2.1 external-share-ready Test Manager test-case review sign-off form for `04-test-case-review/test-case-review-<scope>.md`. |
| `D:\Workspace\west-kowloon\01-requirements\01-source-documents\02-templates\Requirement Review Template.md` / `D:\Workspace\west-kowloon\01-requirements\01-source-documents\02-templates\Test Case Review Template.md` | Canonical content sources for the docx templates; DOCX files may add professional Word layout styling. |

Review-template rules:

- These v2.1 templates are mandatory for future human-facing West Kowloon
  requirement reviews and test-case sign-off reviews.
- Use paired `.md + .docx` for human-facing requirement review and test-case sign-off handoffs.
- Requirement review/sign-off `.docx` files must use `D:\Workspace\west-kowloon\01-requirements\01-source-documents\02-templates\Requirement Review Template.docx`.
- Test-case review/sign-off `.docx` files under `04-test-case-review/` must use `D:\Workspace\west-kowloon\01-requirements\01-source-documents\02-templates\Test Case Review Template.docx`.
- Formal human-facing review/sign-off `.docx` files must be rendered with
  `D:\Workspace\qa-harness\01-system\03-tools\render_review_docx.py`, not the
  generic `D:\Workspace\qa-harness\01-system\03-tools\md_docx.py` converter, so the approved professional Word layout is
  preserved.
- Keep the final sign-off table near the top. The reviewer puts their name or
  signature in `Signature / Confirmation`; do not add a separate `Signed Off By`
  row because it duplicates the signature field.
- Review comments must be summarized into `Review Trail and Version Record`
  before sign-off, including affected case IDs/artifact, version/action, and
  closure evidence. For test-case review comments, update
  `03-test-design/test-cases-<scope>.md`, regenerate the `.xlsx`, and update
  `<package>\03-test-design\CHANGE.md` before marking the comment fixed. When AI changes
  an artifact after comments, keep the review status awaiting human
  re-review/sign-off until the reviewer signs again.
- Use `Open Review Comments` in the conditions/next-step section as the
  simple review gate signal. `None` means no open comments; any actionable
  comment blocks sign-off until the affected artifact is updated and
  re-reviewed.
- Keep the conditions and next-step table at the bottom; do not add a separate
  `Final Decision` section or row.
- Do not use raw HTML tables or forced `<br>` line breaks in review-template markdown.
- QA2 AI review artifacts stay in `03-test-design/.iterations/`; `04-test-case-review/` is only for human/Test Manager sign-off.

---

## [SECTION] Mindmap Storage Convention

Two layers, by scope:

- **Website-level master mindmap** — `D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\01-source-documents\01-mindmap\`
  - `D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\01-source-documents\01-mindmap\mindmap-source.md` — Feishu link, scope notes, export instructions, snapshot inventory.
  - `D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\01-source-documents\01-mindmap\website-mindmap-extract.md` — incremental structured extract; updated as branches are captured.
  - PNG snapshots of the full mindmap (read-only references; large panoramic shots).
- **Per-change narrow captures** — `02-subprojects/02-website/02-modules/<module>/<yyyy-mm-dd>/01-input/02-mindmap/`
  - PNG screenshots scoped to the requirement (e.g., for 2026-05 login dry-run: `注册.png`, `登录1.png`, `登录2.png`, `忘记密码.png`).
  - Must be readable at normal zoom; do not store full-website panoramic shots here.

**Rationale:** The master mindmap covers the entire Website (all branches). Each requirement package consumes only a subset. Placing the full mindmap inside one requirement misleadingly suggests it is that requirement's scope; placing narrow captures at the Website level forces every other requirement to scroll past irrelevant branches. The two-layer split keeps each consumer focused on the right scope.

---

## [SECTION] PRD Section Layout (West Kowloon)

**Location**: `D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\01-source-documents\02-prd\` (Website-level; applies across all requirement packages — they cover the whole Website, not one requirement).

| File | Scope |
|---|---|
| `国际版标准官网 V1.0_总览.pdf` | Product overview, user types, top-nav. Registration/login is a bullet list only. |
| `国际版标准官网 V1.1.pdf` | Membership, ticket detail, account security/deletion, refund/exchange, transfer. **Does NOT contain the main registration/login flow.** |
| `国际版标准官网 - 在线购票.pdf` | Online ticketing. **§3 注册登录 is where the detailed registration/login spec lives.** Authoritative reference (after mindmap) for auth flow specifics. |

When asked about registration/login spec, start with `在线购票.pdf §3`, not V1.1.

---

## [SECTION] HK-Specific Features

The Kasi team is mainland-based; the Website serves Hong Kong. HK-specific features cannot be exercised from the team's environment:

- HK mobile number registration / SMS verification (confirmed 2026-05-15).
- Likely also: HK-specific payment instruments, HK identity providers.

Handling:

- **Write the test case; do not skip.**
- Mark execution status **Deferred — HK-side verification**.
- Include prerequisite assumptions in the case (e.g., "Requires HK SIM"; "Requires Octopus payment account") so HK-side testers can prepare.

This does not extend to features that are genuinely out of scope per the authoritative source. The Deferred treatment is for in-scope-but-unreachable features only.

---

## [SECTION] Operational Notes

- **Chinese PDF extraction**: `pdftotext` (Poppler) silently drops Chinese characters from these PRDs because of the embedded fonts. Use Python `pymupdf` (fitz) instead:

  ```python
  import fitz
  doc = fitz.open(path)
  text = "\n".join(p.get_text() for p in doc)
  ```

  PyMuPDF was installed via `pip install pymupdf` on 2026-05-15.

- **Test case xlsx**: regenerate by **cloning the template file** (`D:\Workspace\west-kowloon\01-requirements\01-source-documents\02-templates\TestCase_Template.xlsx`) and swapping in the data — `shutil.copy` template → target, capture row-2 sample styles, clear sample values, write real rows applying captured per-column styles. Do **not** build a fresh workbook from scratch — the tri-color header (blue `FF2F5597` cols 1-12 / light blue `FF00B0F0` col 13 / purple `FF7030A0` cols 14-20), Calibri 11pt bold white text, thin borders, column widths, and freeze panes are part of the deliverable. Lock files (`~$*.xlsx`) should be deleted, not committed.

- **Feishu export**: Feishu mindmap / Doc do **not** support OPML, Markdown, or CSV export. Only PDF and Word (`.docx`). For mind maps, cropped screenshots at readable zoom are an acceptable fallback.
