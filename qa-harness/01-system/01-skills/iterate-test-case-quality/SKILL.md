---
name: iterate-test-case-quality
description: Use this skill to drive a test case set to a Pass review verdict autonomously, with no human in the loop between rounds. It orchestrates write-test-case → review-test-case → revise-test-case → re-review in a bounded reflection loop, stopping when review returns "Pass" or after a hard cap of 3 revise rounds. Use this when the user asks for "iterative" / "auto-improve" / "loop until Pass" test case generation. Do not use this for one-shot test case authoring (use write-test-case directly).
---

# Iterate Test Case Quality

## Purpose

Turn the existing `write-test-case` + `review-test-case` skills into a closed-loop reflection cycle that converges on a Pass verdict without human intervention between rounds.

The design choice is deliberate: human review still inspects the **final** artifact, but does not arbitrate intermediate rounds. The AI is expected to read its own review feedback, revise, and self-check until it earns Pass — or hits the round cap and surrenders with an honest report.

This is the only skill in the system that chains multiple other skills. Treat it as an orchestrator, not a writer.

## Inputs

Required:

- A requirement / scope description sufficient for `write-test-case` to produce v1 — same inputs that skill takes (requirement doc, mindmap, PRD section, etc.)
- Project context (`project-context.md`) so source-authority order is known

Optional:

- An already-written v1 case file → skip to review step
- An already-written v1 + review file → skip to revise step
- A custom round cap (default 3; never accept > 5)

If invoked in the middle of an existing loop (v2 + r1 already on disk), continue from the next missing step rather than restarting from write.

## Reference Documents

- `../write-test-case/SKILL.md`
- `../review-test-case/SKILL.md`
- `../revise-test-case/SKILL.md`
- `../../07-source-authority.md`

## Workflow

The loop has four states: `WRITE`, `REVIEW`, `REVISE`, `DONE`. Transitions:

```
        ┌──────────────────────────────────────┐
        │                                      │
        ▼                                      │
   ┌─────────┐    ┌──────────┐    ┌─────────┐  │
   │  WRITE  │───▶│  REVIEW  │───▶│ REVISE  │──┘   round++
   └─────────┘    └──────────┘    └─────────┘
                       │
                       │ Pass  OR  round == cap
                       ▼
                   ┌─────────┐
                   │  DONE   │
                   └─────────┘
```

1. **WRITE (round 0)** — invoke `write-test-case` with the supplied inputs. Save initial draft to `03-test-design/.iterations/test-cases-<scope>-v1.md` AND copy to `03-test-design/test-cases-<scope>.md` (the latter is the live "final" pointer, updated every round). Regenerate `03-test-design/test-cases-<scope>.xlsx` from the live md.

2. **REVIEW (any round)** — invoke `review-test-case` against `03-test-design/test-cases-<scope>.md` (the live md). Save output as `03-test-design/.iterations/test-case-review-<scope>-r<N>.md`, where `<N>` is the round number (review of v1 is `r1`, review of v2 is `r2`, etc.).

3. **PARSE Final Decision** — read the line `- Overall result: <verdict>` from the review file's `## [SECTION] Review Summary`. Match exactly (case-insensitive whitespace-tolerant):
   - `Pass` → transition to DONE with status `pass`
   - `Needs Revision` → continue to REVISE
   - `Reject` → continue to REVISE (with stricter handling, see § Reject Handling)
   - Anything else / missing → transition to DONE with status `parse_error`; do not guess

4. **CAP CHECK** — before entering REVISE, check the round counter:
   - If next round would exceed the cap (default 3), transition to DONE with status `cap_reached`
   - Otherwise continue

5. **REVISE** — invoke `revise-test-case` with `(current case file = 03-test-design/test-cases-<scope>.md, latest review = 03-test-design/.iterations/test-case-review-<scope>-r<N>.md)`. Revise updates the live md in place AND snapshots the result to `03-test-design/.iterations/test-cases-<scope>-v<N+1>.md`. Regenerate the xlsx. Round counter increments. Loop back to REVIEW.

6. **DONE** — write a single-page Iteration Report (see § Output Format) summarizing every round's verdict and the final state.

## Reject Handling

If review returns `Reject`, the cause is usually structural (wrong scope, wrong source consulted, fundamentally misunderstood feature). Revise alone cannot fix this. When you see `Reject`:

- Still invoke `revise-test-case` once more
- But also append a `**SCOPE QUESTION**` row to the case file's Open Questions section, quoting the reviewer's Main Concern verbatim
- Do not loop more than once on a Reject. If the next review is still Reject, stop with status `reject_persisted` and surface to user for manual scope decision. Reflexion cannot solve a wrong-source bug.

## Round Counter Semantics

- v1 (initial write) is **not** a round. Rounds start counting from the first revise.
- Default cap is **3 revise rounds** → max artifacts on disk: v1, v2, v3, v4 (cases) + r1, r2, r3, r4 (reviews).
- The cap is a hard stop. Do not silently raise it. If you believe more rounds are needed, stop and tell the user — they can re-invoke with `cap=5` if they accept the cost.

## Cost Awareness

Each full loop round is roughly:

- 1 review LLM call (long-context, reads the full case file)
- 1 revise LLM call (long-context, reads case file + review file, writes new case file)
- 1 xlsx regeneration (cheap, local)

At 3 rounds this is 6+ long-context LLM calls beyond the initial write. **Do not** silently invoke this orchestrator when the user asked for `write-test-case`. The cost difference is real.

## File Layout Convention (qa-harness 03/04)

**Where things go** — this is the canonical convention for any change package under `<project>/01-requirements/02-subprojects/<subproject>/02-modules/<module>/<yyyy-mm-dd>/`:

```
03-test-design/
├── test-cases-<scope>.md       ← CURRENT version (whatever vN is latest)
├── test-cases-<scope>.xlsx     ← CURRENT version (yellow cells = changed vs prev version)
├── CHANGE.md                   ← Cumulative changelog: vN at top, v1 at bottom
├── en/                         ← (optional) translations of current version
│   └── test-cases-<scope>.xlsx
└── .iterations/                ← Audit trail (scanner skips dot-prefixed dirs)
    ├── v1/                     ← Snapshot of v1, created the moment v2 is produced
    │   ├── test-cases-<scope>.{md,xlsx}
    │   └── en/
    ├── v2/                     ← Snapshot of v2, created the moment v3 is produced
    │   └── …
    ├── test-case-review-<scope>-r1.{md,docx}  ← AI review of v1 (stays flat — reviews are round-based)
    ├── test-case-review-<scope>-r2.{md,docx}  ← AI review of v2
    ├── translation-review-<scope>-r1.{md,docx}
    └── iteration-log-<scope>.md
04-test-case-review/
└── test-case-review-<scope>.{md,docx}  ← HUMAN final sign-off review
```

Why this split:

- **03 root = "where do I find the LATEST test cases."** Single stable filename, always latest. Never name it `-v3-final.md` or similar — bumping filenames breaks downstream tooling (gate.py, traceability check, xlsx open paths). The human reader only opens these.
- **`CHANGE.md` at root = cumulative changelog.** Each new version prepends a section. Old sections stay so audit history is in one file. (Per-version-specific CHANGE detail can also live inside `.iterations/vN/` if useful.)
- **`.iterations/vN/` folders = audit-archived snapshots of past versions.** They are created the moment vN is **replaced** by v(N+1) — not while vN is current. The current version lives only at the root. This avoids duplication.
- **`.iterations/test-case-review-*-rN.*` = AI review reports, flat.** Reviews are round-numbered (r1 reviews v1, r2 reviews v2). They stay flat at `.iterations/` root since they cross-reference versions.
- **04 = human sign-off only.** AI review verdicts never go in 04.

## Yellow-Highlight Rule (xlsx cells)

When the iterate loop produces vN+1 (the response to vN's review), apply
visual diff via cell fill so the human reviewer can see at a glance
"what changed this round":

| Yellow color | Meaning | When to apply |
|---|---|---|
| **`FFFF00`** (bright yellow) | NEW or CHANGED cell vs immediately previous version | Cells whose value differs from vN's same row+col when producing vN+1. New rows: fill all populated cells. |
| **`FFFFF2CC`** (light yellow / cream) | Deferred / awaiting product or dev confirmation | Cells that are blocked on a PRD ambiguity, mindmap `?` marker, or open question. Independent of versioning. |
| (no fill / white) | Unchanged + not deferred | Default. |

These two yellows MUST be distinguishable — they signal different
things to the reviewer. `FFFF00` means "I changed this in response to
your last comment"; `FFFFF2CC` means "this can't be tested yet, waiting
on confirmation".

Implementation pattern for the build script:

1. Before producing vN+1, snapshot vN xlsx (load with openpyxl).
2. Generate vN+1 content as usual.
3. For each cell in vN+1, compare value to vN's same row+col:
   - If different and not blank → apply `FFFF00` fill
   - If newly added row → apply `FFFF00` fill to all populated cells
4. Apply `FFFFF2CC` separately based on Deferred status (independent rule).

The two fills must not be combined on the same cell — pick one (FFFF00
wins if both apply, since the change itself is more important to surface).

## CHANGE.md Convention

A `CHANGE.md` lives at `03-test-design/` and is updated by AI whenever
a new version is produced. Format:

```markdown
# Test Cases CHANGE Log

## v<N> — yyyy-mm-dd (current)

**Source dependency**: link to the consolidation doc + the 04 review signoff that drove this version
**Trigger**: which evaluation findings (Q-numbers in 04, finding-IDs in r(N-1)) triggered which changes
**Changes**:
- Added BPP-XXX (capability, reason)
- Modified BPP-YYY's <column> (old → new, reason)
**Yellow cells**: count of FFFF00 cells in v<N> xlsx (sanity check the build script applied diff correctly)
**Previous-version snapshot**: `.iterations/v<N-1>/`
**This-version review**: `.iterations/test-case-review-<scope>-r<N>.{md,docx}`

## v<N-1> — yyyy-mm-dd
…
```

The user reads only the topmost section (the current version). Older
sections are audit. AI must not delete or rewrite old sections —
append at top, leave history below.

## Output Format

After every round, append to the iteration log file at `03-test-design/.iterations/iteration-log-<scope>.md`. Final structure:

```markdown
# Iteration Log: <scope>

- Started: <ISO datetime>
- Finished: <ISO datetime>
- Final status: pass | cap_reached | reject_persisted | parse_error
- Final artifact: test-cases-<scope>.md (vN) + test-cases-<scope>.xlsx
- Total LLM rounds: <N>

---

## Round 0 — Write
- Output: test-cases-<scope>.md (v1) — <N> cases authored
- Duration: <mm:ss>

## Round 1 — Review
- Output: test-case-review-<scope>-r1.md
- Overall result: Needs Revision
- Main concern: <verbatim from review>
- Findings: 2 Critical, 5 Major, 3 Minor

## Round 1 — Revise
- Output: test-cases-<scope>.md (v2) — 4 cases added, 7 modified, 0 removed
- Deferred review items: 1 (out-of-scope addition rejected)

## Round 2 — Review
- Output: test-case-review-<scope>-r2.md
- Overall result: Pass
- Main concern: (none)

---

## Final Verdict

Pass — converged after 1 revise round.

## Deferred / Open Items

| Round | Item | Reason |
|---|---|---|
| 1 | "Add load test for forgot-password" | Out of functional scope; belongs in perf pass |
```

## Orchestrator Rules

- **Never skip the review step.** Even if you think the revise output is obviously better, you must re-review. The whole point is no-human-in-the-loop, which means no Claude-in-the-loop either — review is the only quality gate.
- **Never edit the case file directly.** Call `revise-test-case`. The orchestrator owns chaining, not editing.
- **Never raise the cap silently.** If you want more rounds, stop and ask.
- **Never claim Pass without parsing the actual review verdict string.** The review file's `Overall result:` line is the only Pass signal. Do not infer Pass from "the review looks short" or "I think we addressed everything."
- **Always write the iteration log, even on failure.** `cap_reached` and `reject_persisted` are valid terminal states and need the same audit trail as `pass`.
- **If interrupted mid-loop**, the iteration log file is the source of truth for where to resume. Read it before assuming you need to start from WRITE.

## When NOT to Use This Skill

- Single-shot test authoring → use `write-test-case` directly. Cheaper, faster, and lets human review do its job.
- The reviewer is a human → there is no Pass verdict to parse. Use `write-test-case` + `review-test-case` separately and let the human drive revisions.
- The scope is unclear → resolve scope first via `review-requirement-risk`. Iterating on a wrong-scoped case set just produces a polished wrong answer.
