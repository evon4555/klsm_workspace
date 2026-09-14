# MD / DOCX Hand-Off Convention

## [SECTION] Why this exists

AI-generated review artifacts (requirement consolidation, test case
review, test report, etc.) are written in markdown because markdown is
the form AI reads and writes well. Human reviewers — Test Manager, PM,
product, dev — read those artifacts in Word / WPS, not in raw markdown.
A `.md` table is a wall of pipes; a `.docx` table is a real table.

This document defines how the two formats relate so that AI and humans
can collaborate on the same artifact without either side editing the
wrong copy.

## [SECTION] The Rule

- **`.md` is canonical.** The `.md` file in the package is the source of
  truth that AI reads and writes. Validators and pipelines consume `.md`.
- **`.docx` is a generated review derivative.** Whenever AI hands an
  artifact to a human for review, the AI generates a paired `.docx`
  alongside the `.md`. Generic handoffs use
  `01-system/03-tools/md_docx.py to-docx`; West Kowloon formal
  review/sign-off forms use `01-system/03-tools/render_review_docx.py`.
- **Humans edit the `.docx`.** Test Manager / PM / reviewers do all
  edits in the `.docx`. They must not edit the `.md` directly — those
  edits get overwritten next time the AI regenerates the `.docx`.
- **AI absorbs human edits by converting `.docx` back to `.md`.**
  When the reviewer is done, the AI runs `md_docx.py to-md` and lets
  the converted markdown overwrite the canonical `.md`. From that
  moment forward, the new `.md` is canonical and further AI work
  proceeds from it.

## [SECTION] When This Applies

Apply the hand-off for artifacts that explicitly cross AI ↔ human:

- `02-analysis/requirement-consolidation-*.md` (Step 3.5 gate)
- `04-test-case-review/test-case-review-*.md` (Test Manager final
  sign-off)
- `06-release/test-report-*.md` (release-time report shared with
  stakeholders)
- Any retrospective or escape-analysis doc shared beyond QA

It does **not** apply to:

- Pipeline / system / context / template / skill `.md` files inside
  `01-system/`, `03-context/`, etc. — these are AI-team documents and
  stay markdown-only.
- The test case xlsx — that already lives in its own binary format with
  its own template; do not also produce a docx of it.
- Behave `.feature` files, page object code, etc. — code stays code.

## [SECTION] Mechanics

The converter lives at `01-system/03-tools/md_docx.py` and is backed by
pandoc (bundled inside the venv via `pypandoc-binary`).

For West Kowloon formal requirement-review and final test-case sign-off
documents, use `01-system/03-tools/render_review_docx.py` instead. The generic
converter is acceptable for rough AI working reviews, but must not overwrite
the approved external-share-ready review layout.

```powershell
# AI → human: generate the review copy
python 01-system\03-tools\md_docx.py to-docx <path>\<artifact>.md

# West Kowloon formal review/sign-off DOCX
python 01-system\03-tools\render_review_docx.py <path>\<artifact>.md

# After human edits, AI absorbs the edits
python 01-system\03-tools\md_docx.py to-md   <path>\<artifact>.docx

# Self-check that round-trip preserves semantic content
python 01-system\03-tools\md_docx.py round-trip <path>\<artifact>.md
```

The converter:

- Strips the UTF-8 BOM that pandoc adds to converted markdown (see
  memory: `episode_codex_bom_auth_2026_05_28` — a BOM in a config file
  caused a 3-hour debugging chase; we do not let BOMs in here).
- Forces UTF-8 stdout so PowerShell on a `gbk` codepage does not choke
  on Chinese or arrow characters in printed paths.
- Uses GitHub-flavored markdown as the pivot so tables round-trip.
- Keeps both files side-by-side in the same package folder so
  reviewers see them together; the `.docx` is treated as a generated
  artifact (gitignore-able, but not required — keeping it in git makes
  the review history visible).

## [SECTION] Round-Trip Fidelity

The round-trip is **not byte-identical** and is not expected to be.
Pandoc renormalizes formatting on each pass: tables get column-padded,
horizontal rules expand to full width, paragraph hard-wraps collapse,
`[SECTION]` markers get backslash-escaped. These changes are cosmetic
— the semantic content (paragraph text, table cell content, list items,
code blocks, headers) survives intact.

If you need to verify semantic preservation on a specific artifact:

```powershell
python 01-system\03-tools\md_docx.py round-trip <artifact>.md
```

The diff output is informational. The tool always exits 0 on a clean
round-trip; if pandoc fails, it exits 3.

## [SECTION] Failure Modes To Watch

- **WPS resave loses metadata.** WPS Office is the team's primary
  editor (see memory `feedback_docx_wps_office_compat`). WPS preserves
  pandoc-generated OOXML well, but if a docx was originally a `.doc`,
  use the documented Kwps COM round-trip first.
- **Reviewer edits the `.md` instead of the `.docx`.** This is the
  common discipline failure. Mitigation: file naming. The AI-generated
  `.docx` lives next to the `.md` with the same stem; the reviewer
  picks the `.docx` by default.
- **Two reviewers edit the same `.docx` in parallel.** Out of scope
  for this mechanism — solve by single-owner review windows.
- **AI regenerates the `.docx` between when a reviewer starts editing
  and when they save.** Mitigation: the AI must NOT regenerate the
  `.docx` after handing it over until the reviewer's edits have been
  absorbed back via `to-md`.
- **Raw HTML `<table>` blocks in `.md` are blocked before handoff.**
  Pandoc's gfm reader can silently drop or distort these tables, so
  `md_docx.py to-docx` fails fast by default when a source contains a
  raw `<table>` block. **Always use markdown table syntax** (`| col |
  col |`) for tables in `.md` sources. If legacy recovery is unavoidable,
  pass `--allow-raw-html-tables`, then clean the source back to markdown
  tables before handing it to a reviewer. Column widths are not worth
  losing the table over. (Discovered 2026-06-29 in 08-discount 04 v2
  form; enforced 2026-07-07.)

## [SECTION] Skill / Workflow Integration

- The `consolidate-requirement` skill must call `to-docx` after
  drafting the consolidation `.md`, so the Test Manager receives both.
- The Step 3.5 gate is satisfied when (a) the consolidation `.md`
  reaches **Signed Off** status, AND (b) any reviewer-edited `.docx`
  has been absorbed back into the `.md` via `to-md`.
- For `04-test-case-review/` and `06-release/test-report-*.md`, the
  same pattern applies: AI drafts `.md`, AI emits `.docx`, reviewer
  edits `.docx`, AI absorbs back to `.md` before downstream steps
  consume the artifact.

## [SECTION] Signed Doc Structure Convention

For any review/sign-off docx (consolidation, test-case review, test
report, escape-analysis report, etc.), the document MUST be ordered
**information at top, decision list at the very bottom**:

```
┌─ Metadata table (status, scope, package) ───┐
│ Revision History (pre-filled sig row)       │   ← top, classical email-style position
├──────────────────────────────────────────────┤
│ All informational content:                  │   ← signing means you have read these
│   - AI conclusion / summary                 │
│   - Scope / sources / differences           │
│   - Anything reviewer needs as context      │
├──────────────────────────────────────────────┤
│ Decision list (Q-1..Q-N tables)             │   ← absolute last, the actions to take
│   - Q-X table with options (a)/(b)/(c)      │
│   - U-X table for assumptions to confirm    │
└──────────────────────────────────────────────┘
```

**Why this order**: the **decision list at the bottom** is what
implies "the reviewer has read everything above". When the reviewer
hits the Q-X table at the end, they have the full context to answer.
The Revision History (with the pre-filled signature row) stays at
top — classical email/document position — so signature status is
visible at a glance without scrolling. The decision list is the
action item; the signature row is the receipt.

Putting decisions before information would make the reviewer answer
before they have context. Burying the signature row at the bottom
would hide signoff status from at-a-glance reading.

### Pre-filled signature row pattern

The AI pre-fills two rows in the Revision History at creation time:

```markdown
| Date | Author | Change | Status |
|---|---|---|---|
| YYYY-MM-DD | QA1 (AI) | <what AI did> | Done |
| YYYY-MM-DD | <reviewer name + role> | _Fill verdict here (placeholder)_ | **Awaiting Sign-Off** |
```

The reviewer signs by editing the placeholder text in the Change
column and changing "Awaiting Sign-Off" → "Signed Off" (or "已确认"
in zh-CN docs). They do **not** add a new row. The row is positioned
for them.

**Status vocabulary** (for the Status column of the AI's row):

- `Done` / `已完成` — AI completed its task (drafting, generating,
  reviewing). Does NOT mean "the doc is signed".
- AI must never write `Signed Off` for its own row. Only the reviewer
  fills that.

**Drop the redundant "§ Sign-off" instructions section.** With the
pre-filled row, the ceremony is "edit two cells, save" — no separate
instructions section needed (a one-line note above the table is
enough).

## [SECTION] Human Review DOCX Format Quality

When generating a human-facing `.docx`, do not treat "successfully
converted" as "ready to hand off". The `.docx` must be readable as a
review form in Word/WPS.

Rules:

- If a project provides a human-facing review template under
  `<project>/01-requirements/01-source-documents/02-templates/`, use it for
  the `.docx` handoff. The project template wins over ad hoc generated Word
  layout.
- Use a clean prior accepted artifact as the structural reference when one
  exists in the same project/package family.
- Prefer simple markdown tables for metadata, revision history, summary, and
  decision lists. Do **not** use raw HTML `<table>` blocks in handoff sources.
- Avoid forced line breaks such as `<br>` inside decision-list table cells.
  Prefer concise semicolon-separated options so Word/WPS -> markdown absorption
  is less likely to come back as an HTML table.
- Do not copy a known-poor legacy form just because it is the nearest previous
  file. If the prior form used raw HTML tables or rendered poorly, treat it as
  an anti-reference and rebuild the source with markdown tables.
- The active signature/status table stays near the top; the decision list stays
  at the bottom.
- After `to-docx`, open the generated file with `python-docx` and verify it has
  the expected tables and signature row before telling the user it is ready.

West Kowloon note: the 2026-06-25 discount-module test-case review sign-off
form is a known poor-format example because its decision list was authored as a
raw HTML table. Use the cleaned markdown-table structure from later sign-off
forms instead.

## [SECTION] Translation Cases

Translations frequently ride on top of this hand-off (e.g. producing
an EN docx of a ZH artifact for international stakeholders). When that
happens:

- The translated artifact (whether .md or .xlsx) MUST be reviewed by
  [`01-skills/review-translation-quality`](./01-skills/review-translation-quality/SKILL.md)
  before delivery. This is non-optional — see that skill's "When To Use"
  section for the rule.
- A clean validator PASS on the translated xlsx does **not** mean the
  translation is good. The validator checks schema/IDs/yellow-rows only;
  it tells you nothing about whether the words match the source.
- Place translations in a `/en/` (or `/zh-HK/` etc.) subdirectory next
  to the source so the signoff gate's `glob` (non-recursive on
  `02-analysis/`) does not treat them as a separate consolidation
  requiring its own signoff. For `03-test-design/` (which uses `rglob`),
  use the same filename as the source so they pair to the same scope.
