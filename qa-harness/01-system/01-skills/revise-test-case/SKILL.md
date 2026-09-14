---
name: revise-test-case
description: Use this skill to revise an existing test case set based on the findings of a prior review. It consumes the original test case file plus the review output, applies the review's Required Actions and Recommended Additions, marks the diff visibly, and regenerates derived artifacts (xlsx). Designed to be invoked automatically by iterate-test-case-quality, or manually with a hand-written review.
---

# Revise Test Case

## Purpose

Close the gap between a test case set and the issues raised in its review. The revise step is what turns review feedback into shipped quality — without it, review output is just a complaint list.

The goal is **only** to apply the review's findings. Do not invent improvements the reviewer did not request. Do not re-do scope. If the reviewer was wrong, surface it as an open question; do not silently override.

## Inputs

Required:

- Original test case file (markdown produced by `write-test-case`, e.g. `test-cases-<scope>.md`)
- Review file (markdown produced by `review-test-case`, e.g. `test-case-review-<scope>.md`)

Optional but used when present:

- The authoritative source the original cases were derived from (PRD section, mindmap, etc.) — needed if the reviewer's Recommended Additions reference behavior the writer didn't see
- Project template (`<project>/01-requirements/01-source-documents/02-templates/TestCase_Template.xlsx`) if the project has one
- Previous approved test case version, when the input is v2+ or part of a requirement-change update
- `project-context.md` — for source-authority order and template precedence

If the review file is missing a `Final Decision` or `Findings` section, stop and report — there is nothing to apply.

## Reference Documents

When available, align with:

- `../../01-quality-principles.md`
- `../../05-evidence-standard.md`
- `../../07-source-authority.md`
- `../../templates/test-case-template.md`
- `../write-test-case/SKILL.md` § Output Format (for column structure)
- `../review-test-case/SKILL.md` § Output Format (for finding semantics)

## Workflow

1. **Parse the review.** Extract from the review file:
   - Coverage Review rows with status `Partial` or `Missing` → these become required new cases or expansions
   - Findings rows (Critical / Major / Minor) with `Suggested Fix` → these become required edits to existing cases
   - Recommended Additions → these become new cases at the priority the reviewer suggested
2. **Cross-check against the authoritative source.** For each Required Action that adds scope, confirm the scope exists in the authoritative source. If not, drop it and log it as an open question; do not invent scope on the reviewer's say-so alone.
3. **Apply edits in place** to the original case file:
   - For v2+ revisions, match the previous approved version's row structure,
     step wording style, expected-result granularity, enum labels,
     owner/environment conventions, and bold-marker convention unless the
     review explicitly requests a whole-file format migration
   - Modify existing cases (steps, expected results, priority, evidence) as the Findings instruct
   - Append new cases at the end of the table, continuing the existing ID sequence (e.g., if last was `TC-023`, next is `TC-024`; never `TC-NEW-1`)
   - Do **not** renumber existing cases. The IDs are external references.
   - Remove cases the reviewer flagged as duplicate/invalid, and record the removal in Revision History
4. **Mark the diff visibly** so the next reviewer (human or AI) can see what changed without running git diff:
   - **New case** → wrap the entire case row's content in `**…**` (ID, title, steps, expected, all bold)
   - **Modified field** → bold only that field's new value (e.g., `Expected Result: **400 error with message "phone format invalid"**`), not the whole row
   - **Unchanged cases** → leave plain. Do not bold anything that wasn't changed.
   - This is the only acceptable use of bold in the case file; do not use it for emphasis elsewhere.
5. **Update Revision History** at the top of the file:
   ```markdown
   ## [SECTION] Revision History
   | Version | Date | Reviewer | Round | Summary |
   |---|---|---|---|---|
   | v2 | 2026-05-29 | review-test-case (AI) | 1 | Added 4 negative cases for forgot-password OTP; fixed expected results in TC-007/011 per Critical findings |
   ```
6. **Regenerate the xlsx** if the project uses one. Follow `write-test-case/SKILL.md` § "xlsx regeneration procedure" exactly:
   - `shutil.copy(template_path, target_path)` to preserve template styles
   - Re-apply per-column styles from the sample row
   - Do **not** create a fresh `openpyxl.Workbook()`
7. **List unresolved review items.** If any Finding could not be applied (because it conflicts with the authoritative source, or requires data the case file doesn't have), append a "Deferred Review Items" section listing them with reasons. Do not pretend to have applied them.

## Output Format

The output is **the original case file revised in place**, not a new file with a different name. Same path, new content, with:

- Revision History row prepended (after the scope summary)
- Modified / new cases bolded per § Workflow step 4
- Same column structure, same template formatting, and same writing style as
  the previous approved version for v2+ work
- xlsx regenerated next to the markdown

Additionally, return a brief revise log to the caller:

```markdown
# Revise Log

- Round: <N>
- Source review file: <path>
- Applied: <count> findings, <count> additions
- Deferred: <count> items (see § Deferred Review Items in the case file)
- xlsx regenerated: yes / no / n/a
- Open questions raised: <count>
```

The orchestrator reads this log to decide whether to send the revised file back for another review round.

## Revise Rules

- **Only apply what the reviewer asked for.** No silent improvements, no scope creep, no style cleanup.
- **Never renumber existing cases.** Append; don't rewrite IDs.
- **Preserve prior-version style for v2+.** New and modified rows must match
  the previous approved version's row format, step style, expected-result
  style, enum labels, field granularity, and bold-marker convention.
- **Bold marks the diff, nothing else.** A revised file with no bold means nothing changed (and you probably didn't do your job).
- **Authoritative source still wins.** A reviewer recommending out-of-scope cases gets a Deferred row, not a new case.
- **Preserve template fidelity.** xlsx column structure, header styles, freeze panes, and merged cells must survive regeneration intact.
- **Do not invoke this skill for the first draft.** Use `write-test-case` for v1. Revise is for v2+.
- **Do not re-review your own output.** That is `review-test-case`'s job; the orchestrator chains them.

## Wording-Fix Rule (mandatory rewrite, not punctuation surgery)

When the review's Findings include any Description-Wording or Steps-Wording pattern from
`write-test-case/SKILL.md § Description Wording Rules` or `§ Test Steps Wording Rules`
(the `;` / ` - ` / `+` / `:` / `and`-chain / role-switch / atomicity family),
**do not fix the punctuation in place**. Rewrite — or split — the affected case from scratch.

### Why

Every one of those banned patterns is a symptom of two cases (or two checkpoints) crammed into one row.
Deleting the `;` or swapping `;` for `.` without rethinking the case leaves the smashed-together
content untouched: the reader still cannot tell what the single scenario is, and the reviewer will
raise the same finding again next round. Iterate loops die here.

### What to do instead

For each affected case, follow this sequence:

1. **Extract the checkpoint list.** Read the Description, Steps, and Expected Result together and
   list every distinct assertion the case is trying to make.
2. **Decide split vs relocate for each item:**
   - Two subject categories (guest vs logged-in, EMAIL vs MOBILE, admin vs user) → **split into
     separate cases**, one per category. Never a single case with an "As X … As Y …" step sequence.
   - Two data variants of the same scenario (wrong OTP vs correct OTP, valid vs invalid captcha) →
     **split into separate cases**, one per outcome. Never a single case with a `wrong/correct` slash.
   - Multiple independently observable checkpoints of the same scenario → **relocate to Expected
     Result as separate bullets**. Description stays as one sentence.
   - "Verify"/"observe"/"confirm" inside Steps → **relocate to Expected Result**. Steps are actions
     only.
3. **Rewrite the Description from scratch** as one grammatical "Verify …" sentence covering one
   scenario. Apply the Reader Test from `write-test-case/SKILL.md § Reader test` before saving.
4. **Rewrite the Steps from scratch** with one atomic action per numbered line, one persona for
   the whole case, one branch/data-variant for the whole case.
5. **Apply the diff-mark rule** — the rewritten Description / Steps / Expected Result cells count
   as modified fields (bold the new value); any newly created split-off case counts as a new case
   (bold the whole row).

### Forbidden shortcuts

- Do **not** replace `;` with `.` or `,` and call it done.
- Do **not** delete the offending clause to silence the reviewer while losing coverage.
- Do **not** move a `;`-chained clause into Expected Result verbatim when it was actually a second
  scenario — that just relocates the bug.
- Do **not** claim the finding is Minor and merge Description + Steps + Expected together to make it
  "read easier" — the columns exist to separate what/how/pass, keep them separate.

### Record in Revision History

When you split one case into N, note the split in Revision History as
`Split TC-XXX into TC-XXX + TC-YYY (Description-wording pattern: <the pattern>)`.
When you rewrite in place, note it as
`Rewrote TC-XXX (Description|Steps) to satisfy wording rules; coverage unchanged`.
This lets the next review round trace intent instead of guessing at bold cells.
