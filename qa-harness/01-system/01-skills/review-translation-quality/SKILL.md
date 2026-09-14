---
name: review-translation-quality
description: Use this skill whenever you have generated or modified a translation of an existing artifact (test case set, requirement consolidation, test report, review note, etc.) — BEFORE reporting it as done. It is a defect-finding pass that compares the translation against the source for fidelity, terminology consistency, style consistency, identifier preservation, idiomatic naturalness, and format preservation. The output is a structured list of issues with cell / line references so they can be fixed in one pass.
---

# Review Translation Quality

## When To Use (Mandatory After Any Translation)

This skill is **mandatory** after producing any translated artifact in
this harness — it is not optional. The rule is: **if you just ran a
translation step (md → md in another language, or wrote a manual
translation), you must run this review BEFORE telling the user the
translation is ready.** Reporting "translation done" without running
this review has caused real defects in West Kowloon (`08-discount/
2026-06-25/03-test-design/en/test-cases-bank-card-priority-purchase.xlsx`
v1, 2026-06-27 — translation drift, style inconsistency, lost
identifiers).

Trigger examples:

- You generated `<artifact>.en.md` from `<artifact>.md` (or any
  source-language ↔ target-language pair)
- A reviewer asked for "an English version" / "a translated version"
- You produced a multilingual export of a test case set, review note,
  consolidation doc, test report, or release artifact
- You used `md_docx.py` round-trip in a context where translation
  was involved (rare but possible)

This skill does NOT apply to:

- Bilingual originals that were authored as bilingual from the start
- Code / page-object / config files (translation is not in scope)
- Trivial single-sentence translations (run the checks in your head
  but don't produce a full report)

## Purpose

Find translation defects before delivery. Reading the translated
artifact in isolation makes most issues invisible — you need a
**side-by-side comparison** against the source. This skill enforces
that comparison and structures the findings.

## Inputs

- Source artifact (the original-language version)
- Translated artifact (the target-language version)
- Project terminology references, in priority order:
  - Project context: `<project>/01-requirements/00-project-overview/`
  - Existing English in the workspace (other `01-system/*.md` files,
    other project's English artifacts) — for term consistency
  - PRD / functional spec source documents that may include a glossary
- (Optional) Previous translation of the same scope for term continuity

## Reference Documents

- `../../12-md-docx-handoff.md` — the md ↔ docx hand-off mechanism that
  translations typically ride on top of
- `../../03-tools/md_docx.py` — the converter; pandoc-based
- Existing reviewed translations in the workspace for style benchmark

## Workflow

0. **(Pre-translation only — before any translation begins)** **Extract
   the source glossary FIRST.** Build a `term → translation` mapping
   from the source artifact + project glossary (if present at
   `<project>/01-requirements/00-project-overview/translation-glossary.md`).
   Translating before doing this leads to identifier drift across
   columns (the canonical defect: BPP-024 EN v2 2026-06-27 — Partner
   qualifier preserved in Expected column but dropped in Data column,
   because the glossary was built reactively from Expected only).
1. **Load both artifacts.** Map source rows / sections to target rows /
   sections by stable identifier (test case ID, section number, table
   row position). Refuse to proceed if mapping is ambiguous.
2. **Build a comparison view.** For tabular artifacts (test cases): one
   row per identifier, showing source and target side by side for the
   columns most prone to translation drift (typically Steps, Expected
   Result, Description, Notes / Comments).
3. **Run the 8 checks below.** For each finding, record:
   `<location> | <category> | <issue> | <suggested fix>`.
4. **Categorize findings by severity:**
   - **Critical**: changes the semantics of the test / requirement /
     decision (e.g., "verify X" translated as "verify NOT X")
   - **High**: lost identifier, lost technical term, added content not
     in source, removed content from source
   - **Medium**: style inconsistency, terminology inconsistency,
     awkward target-language phrasing that obscures meaning
   - **Minor**: cosmetic phrasing, missing articles, capitalization,
     consistent-but-not-ideal word choice
5. **Produce report.** Use the Output Format below.
6. **Recommend fix path:**
   - If only Minor: ship as-is, log findings for future style guide
   - If Medium+: produce v2 fixing all Medium+, ship v2

## Quality Categories (the 8 checks)

| # | Check | What to look for |
|---|---|---|
| 1 | **Source-target alignment** | Every source sentence has a target sentence; no added content, no dropped content. Watch especially for AI helpfully adding context that the source didn't have. |
| 2 | **Terminology consistency** | Same source term translated the same way every time. Build an implicit glossary from first usages; check later usages match. |
| 3 | **Style consistency** | One mood (imperative vs declarative), one person (1st/2nd/3rd), one tense across same-section content. Mixing 祈使句 and 第三人称 within Test Steps is the canonical defect. |
| 4 | **Identifier preservation** | Test case IDs, F-codes, U-codes, Q-codes, partner names ("Partner A"), card numbers, mid values, prices — all preserved verbatim. Partner identifier dropping (e.g. "Partner A Diamond" → "Diamond") is the canonical defect. |
| 5 | **Precision preservation** | No silent simplification. "priority-purchase benefit" must not become "priority benefit". Multi-word concepts stay multi-word. |
| 6 | **Target-language idiom** | No calques. Hyphenated compounds that don't exist in the target language (e.g. "bound-at time" — invalid English) must be replaced. No formula-like fragments like "(80 lowest)" — write the full phrase. |
| 7 | **Format preservation** | Markdown structure (tables, lists, emphasis, line breaks), embedded code spans, `<br>` line breaks inside cells, fullwidth punctuation in CJK context, all preserved. |
| 8 | **Mock data fidelity** | Test data values (email addresses, card numbers, prices, dates, URLs) are preserved exactly. Names of test users / partners / events follow the project's translation choices and are consistent throughout. |

## Output Format

```markdown
# Translation Quality Review — <scope> — <source-lang> → <target-lang>

| Field | Value |
|---|---|
| Source artifact | <path> |
| Target artifact | <path> |
| Reviewer | QA2 (AI) — review-translation-quality skill |
| Review Date | <yyyy-mm-dd> |
| Verdict | Pass / Pass with revisions / Reject |

## Summary

- Total items compared: <N>
- Findings: <C> Critical / <H> High / <M> Medium / <m> Minor
- Recommendation: <ship-as-is | produce v2 fixing Medium+ | reject and re-translate>

## Findings

### Critical (semantic defects)

| Location | Issue | Source | Target | Suggested Fix |
|---|---|---|---|---|
| BPP-007 Expected | added content not in source | "显示「未匹配到 BIN」" | "Shows \"BIN not matched, please verify the card number\"" | Drop "please verify the card number" — source doesn't say it |

### High (lost identifiers / drift)

(same table shape)

### Medium (style / terminology / awkwardness)

(same table shape)

### Minor (cosmetic)

(same table shape)

## Glossary Built From This Review

| Source term | Chosen target translation | Notes |
|---|---|---|
| 合作方甲 | Partner A | Keep partner letter in target |
| 优先购权益 | priority-purchase benefit | Do NOT shorten to "priority benefit" |
| 我的权益身份 | My Benefit Identities | First usage may include "(我的权益身份)" parenthetical |

(Glossary should be reused by future translations in this project — promote
to project `00-project-overview/` if it stabilizes.)

## Recommendation

- Decision: <Pass | Pass with revisions | Reject>
- Reason: <one paragraph>
- If Pass with revisions: list of fixes for v2, in execution order
- Follow-up Owner: <the QA1 / translator who will revise>
```

## Quality Rules

- **Honest checks, not rubber stamps.** Compare side-by-side. If you
  skip the comparison and rely on memory, you will miss defects — this
  has happened.
- **A clean validator PASS is not a translation quality signal.** xlsx
  schema, row count, and ID format checks tell you nothing about
  whether the words are right.
- **Categorize by user-visible impact**, not by syntactic surface:
  "Diamond" instead of "Partner A Diamond" is High (lost identifier
  means the reader doesn't know which partner), not Minor.
- **Build the implicit glossary as you go.** If you see "合作方甲" → 
  "Partner A" in row 1 and "Diamond" alone in row 24, the row-24
  translation is wrong — even if "Partner A Diamond" was never
  explicitly defined as the glossary entry.
- **Apply this skill to your OWN output, not just to others'.**
  Self-review is non-optional after producing a translation.
- **The output should be actionable.** Each finding must point at a
  specific cell / line and suggest a concrete fix. Vague findings
  ("the English feels off") have no fix path and waste reviewer time.

## Anti-patterns to flag

These are recurring translation defects in this harness, captured
from real incidents:

- Adding helpful explanatory text not in source ("please verify the
  card number" added to "BIN not matched")
- Dropping the partner / module qualifier when reusing a noun
  ("Partner A Diamond" → "Diamond")
- Inventing English compound words from a literal translation
  pattern ("绑定时间" → "bound-at time" is not English)
- Mixing imperative ("Click +") with third person ("user1 clicks +")
  within the same Test Steps column
- Compressing a 4-word concept to 2 words to save space
  ("priority-purchase benefit" → "priority benefit")
- Formula-shaped fragments instead of full phrases
  ("(80 lowest)" instead of "(price 80, the lowest)")
