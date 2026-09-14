# Change Management

How this team handles **requirement changes** without losing history and
without leaving stale automation behind. Companion to `08-our-pipeline.md`.

The core principle: **never overwrite, always version + diff**. Requirements
change 1-3+ times per feature; each change has its own audit row.

---

## [SECTION] What changes, and what to version

| Artifact | Versioning model | Where |
|---|---|---|
| **Source documents** (figma, mindmap, PRD) | New ISO-date dir, original kept | `01-requirements/02-subprojects/<subproject>/01-source-documents/` or change-package `01-input/` |
| **Test cases (xlsx + md)** | Timestamp-suffixed file alongside the live one | `02-modules/<module>/<yyyy-mm-dd>/03-test-design/test-cases-<scope>_<ISO-date>.xlsx` |
| **`.feature` files** | Soft-delete then hard-delete (see Soft delete) | `02-automation/01-features/` and `02-automation/01-features/deprecated/` |
| **Page objects / API helpers** | Soft-delete same as features | `02-automation/03-src/.../deprecated/` |
| **CHANGE.md** | One per change, mandatory | `02-modules/<module>/<yyyy-mm-dd>/01-input/CHANGE.md` |

---

## [SECTION] Naming convention

**ISO 8601 dates** everywhere:  `2026-06-02`, not `2026/6/2`, not `6-2-26`,
not `20260602`. Sortable, no slash-in-path issues, no ambiguity.

For multiple changes on the same day add a suffix:  `2026-06-02-a`,
`2026-06-02-b`. (Rare; usually 1 change/day max.)

---

## [SECTION] Each change must have a CHANGE.md

At `01-input/<change-date>/CHANGE.md`:

```markdown
# Change 2026-06-02

**Why:**       PM decided to add "Remember me" checkbox on login
**Source:**    ZenTao #4892 (or: customer feedback / compliance ticket / bug #X)
**Approver:**  王一凡 (test manager)
**Effective:** 2026-06-15 release
**Scope:**
  - Modify: AUTH-013, AUTH-014
  - Add:    AUTH-077
  - Deprecate: AUTH-022 (login auto-clear behavior removed)
```

**Why this is mandatory**: 6 months later, looking at a date folder, you
need to know WHY. Git commit messages decay; CHANGE.md is part of the
artifact and lasts forever.

**Until ZenTao integration is built** (per `08-our-pipeline.md` step 8),
fill `Source:` by hand — ZenTao link OR meeting note OR Slack thread URL.

---

## [SECTION] Soft delete policy (NEVER hard-delete on first change)

When a test case is removed by a requirement change:

```
Day 0 (change merged):
  01-features/authentication.feature           ← updated, drops the removed scenario
  01-features/deprecated/authentication_v1_2026-05-22.feature   ← snapshot of old version

Day +14 (after 1 sprint of clean runs):
  01-features/deprecated/authentication_v1_2026-05-22.feature   ← still there

Day +30 (after 2 sprints of clean runs, no rollback):
  hard-delete the deprecated copy
```

**Why the buffer**: requirements roll back. Today's "no longer needed"
becomes next Tuesday's "wait we changed our minds." Soft delete saves
the work; hard delete forces re-authoring.

Page objects and helper code follow the same policy.

---

## [SECTION] Test case ID lineage

**Rule: keep the same ID, mark the revision date.**

When `AUTH-013` changes meaning (e.g. "show toast on login fail" →
"show modal on login fail"):

- **Do** keep ID = `AUTH-013`
- **Do** add `last_revised: 2026-06-02` to the case row
- **Don't** retire `AUTH-013` and create `AUTH-013-v2`

**Why**: dashboard trend charts join on case ID over time. New IDs
break continuity for no real benefit.

**Trade-off acknowledged**: "AUTH-013 failed" on day N+1 means a
different thing than on day N-1. Dashboard mitigates this by drawing
a vertical line on the trend chart at every `last_revised` date so
the reader sees "context changed here." (UI work: todo — track in
`ApiMonitorPage.jsx` trend section.)

---

## [SECTION] The RAG-style maintenance loop

When a new xlsx version lands, automation must NOT silently rot. We
run a maintenance scanner that compares old vs new and surfaces work:

```
Trigger: a new test-cases-<scope>_<ISO-date>.xlsx is committed
        ↓
1. Diff vs previous version
   → "added: [AUTH-077]  removed: [AUTH-022]  modified: [AUTH-013, AUTH-014]"
        ↓
2. For each case in the diff:
     added    → find matching .feature scenario by Scenario ID prefix
                if missing → write TODO stub scenario + page object skeleton
     removed  → find scenario → mark for soft-delete (move to deprecated/)
     modified → find scenario → run text diff on steps → flag for human review
        ↓
3. Write maintenance_report.md:
   - "TODO: 1 new case needs automation (AUTH-077)"
   - "Deprecate candidate: 1 scenario (AUTH-022)"
   - "Drift: 2 scenarios have step text different from updated case"
   - "Workload estimate: ~3h"
        ↓
4. Dashboard "Change Workload" page reads the report
   → tracks effort spent per change for management reporting
```

### Matching key (which .feature scenario belongs to which case)

Traceability, implemented in `01-system/03-tools/check_traceability.py`:

1. Put the full Test Case ID at the start of the Scenario name, for example
   `Scenario: SIT-TC-WEB-AUTH-013 user sees error on bad password`.
2. Do not add Test Case ID as a Behave tag for new automation.
3. Explicit `@SIT-TC-...` tags are accepted only as a legacy fallback for old
   feature files and historical dashboard rows.

This is documented in memory `reference_bdd_traceability_convention`.

### Tool to build (not yet implemented)

Add to `01-system/03-tools/`:
- `diff_xlsx_versions.py` — compare two xlsx test case files, emit JSON of added/removed/modified
- `maintenance_scan.py` — wraps diff + cross-references `02-automation/01-features/` + writes maintenance_report.md

These should run automatically when a new dated xlsx is committed (git
hook or CI workflow).

---

## [SECTION] Test case version style continuity

Severity: **High**.

When reviewing or revising a later version of a test case set, the previous
approved version is the style baseline. A new AI pass, reviewer pass, or
requirement-change pass must preserve the prior version's format and writing
style unless the project owner explicitly asks for a format migration.

This applies even when the new content is functionally correct. Format/style
drift is a review finding because mixed Claude/GPT wording and row structure
make the workbook harder to maintain.

Required behavior for v2+ changes:

- Compare the new version against the previous approved `.xlsx` / `.md`
  before approving.
- Preserve column order, field names, enum labels, owner/environment values,
  ID format, priority/risk label style, line breaks, numbering style, and
  step/expected-result granularity.
- For modified cases, keep unchanged fields byte-for-byte where possible; only
  rewrite the fields that actually changed.
- For added cases, copy the style of the nearest same-module or same-flow case
  in the previous version.
- Do not mix narrative styles inside one workbook. If existing rows use concise
  imperative steps, new rows use the same style; if existing rows use bold diff
  markers only for changed fields, do not add bold for emphasis.
- If the new requirement truly needs a different structure, record the format
  migration explicitly in `CHANGE.md` / Revision History and apply it to the
  whole workbook consistently.

Review outcome rule: a v2+ test case set with unexplained format/style drift
must be marked **Needs Revision** even if coverage is otherwise acceptable.

---

## [SECTION] Visual diff convention for regenerated xlsx

When a requirement change triggers test case regeneration, the new
`test-cases-<scope>_<ISO-date>.xlsx` must **visually mark what changed**
so reviewers don't need to diff two files manually.

This is the output format spec for `diff_xlsx_versions.py` (planned
above) when it produces the regenerated xlsx.

### Color rule

| What changed | What to color | Color |
|---|---|---|
| One cell modified | that single cell | 柠檬黄 `FFFACD` |
| Multiple cells in a row modified | each modified cell | 柠檬黄 `FFFACD` |
| Whole row's meaning changed (re-authored) | the entire row | 柠檬黄 `FFFACD` |
| New row added | (no color requirement — leave to tool author) | — |
| Row removed | row does not appear in new xlsx; tracked in `maintenance_report.md` | — |

**One color, one purpose**: 柠檬黄 = "this cell differs from the previous
version." Don't reuse it for warnings, TODOs, or anything else.

`FFFACD` is the openpyxl / Excel hex code (no `#` prefix). In code:

```python
from openpyxl.styles import PatternFill
YELLOW = PatternFill(start_color="FFFACD", end_color="FFFACD", fill_type="solid")
cell.fill = YELLOW
```

### Comment rule

Every yellow cell **must carry an openpyxl `Comment`** that explains
**why** the change was needed. The comment is the audit trail — a
reviewer reading the xlsx alone (without the repo) must understand the
reason from the comment.

Good comment content:

- The actual reason ("PM added 'Remember me' checkbox per ZenTao #4892")
- A short before → after if it clarifies ("was: 6-char password; now: 8-char min")
- A pointer to the CHANGE.md if the reason is long ("see 01-input/2026-06-15/CHANGE.md")

Bad comment content (do **not** write these):

- "Changed" / "Updated" / "Modified" — says nothing about why
- "Auto-generated by diff_xlsx_versions.py" — tooling noise, not reason
- Just a timestamp or author — those are in git, not useful here

A whole-row change can have one comment on the row's ID cell rather than
one per cell, as long as the reason is the same across the row.

### Why this exists

xlsx is the artifact PMs, test managers, and external reviewers actually
open. They will not run a diff tool. The colored cells + comments make
"what changed and why" answerable in 10 seconds without leaving Excel /
WPS.

This also feeds the [Test case ID lineage](#section-test-case-id-lineage)
rule: ID stays the same, `last_revised` date moves forward, and the
yellow + comment is the proof of what moved.

---

## [SECTION] Human-visible case change audit

For post-review or post-sign-off test-case add, modify, remove, or scope
adjustment work, `CHANGE.md` and git history are not enough. The reviewer must
be able to open the current `.xlsx` and `.docx` and see what changed.

Required visible trail:

| Surface | Required record |
|---|---|
| `03-test-design/test-cases-<scope>.xlsx` | `Audit Trail` sheet with date, actor, change type, reason, affected case IDs, current scope impact, and evidence |
| `04-test-case-review/test-case-review-<scope>.docx` | `Review Trail and Version Record` row with the same affected case IDs and closure evidence |
| `05-execution/02-automation-assessment/automation-assessment-<scope>.xlsx` | Matching `Audit Trail` row when the automation assessment already exists |
| `05-execution/02-automation-assessment/automation-assessment-review-<scope>.docx` | Matching review trail row when automation assessment review already exists |

Use `01-system/03-tools/record_testcase_change.py` after the current workbook
has been updated. Run `01-system/03-tools/check_testcase_audit_trail.py` or the
full `gate.py` before closeout. MD-only audit notes are not acceptable because
the human review surface is `.xlsx` and `.docx`.

---

## [SECTION] Workload tracking

Every change creates work; we track it so management sees true cost.

Fields captured per change (in `CHANGE.md` + `maintenance_report.md`):

| Field | Where it lives |
|---|---|
| Cases added / removed / modified | `maintenance_report.md` (auto from diff) |
| Estimated hours to absorb | `CHANGE.md` "Effort:" line (filled by QA after scan) |
| Actual hours spent | Updated post-fact by QA at close |
| Linked PRs | git log filtered by `Change: 2026-06-02` commit trailer |
| Run dates after change | dashboard `/api/runs` filtered by date range |

Dashboard surfaces a **"Change Workload"** page (todo) aggregating
these across all `CHANGE.md` files in the project. Lets the team
report "we absorbed 4 PM changes this sprint, total 23h of QA cost."

---

## [SECTION] Quick decision tree for a new change

```
PM tells you "X needs to change"
        ↓
Is the source documented?  (PRD updated? ZenTao ticket?)
        N → push back, get it documented first
        Y → ↓
Create 01-input/<ISO-date>/ + CHANGE.md
        ↓
Drop new figma/mindmap/PRD under that dir
        ↓
QA1 re-runs write-test-case + iterate-test-case-quality
       (skill auto-saves new xlsx with _<ISO-date>.xlsx suffix)
        ↓
Human Test Manager signs off (04-test-case-review/)
        ↓
Run diff_xlsx_versions.py + maintenance_scan.py
        ↓
For each item in the maintenance report:
   - Write missing automation
   - Soft-delete deprecated automation
   - Resolve drift items
        ↓
Update CHANGE.md "Effort:" with actual hours
        ↓
Run gate.py → must PASS before merging
```

---

## [SECTION] What this doesn't cover yet

- **Hard-delete cron**: nothing today scans `deprecated/` for files older
  than N sprints and offers to delete. Add when accumulation hurts.
- **Cross-project change propagation**: if one change affects multiple
  projects (e.g. a shared SDK), each project needs its own CHANGE.md.
  We don't auto-link them.
- **ZenTao push-back**: change "Effort actual" should flow back to ZenTao
  for time tracking. Waits for the future ZenTao integration.
- **Drift detection over time**: if a case wasn't touched but the live
  product changed underneath, we won't catch it from xlsx diff alone.
  Needs a separate "production behavior monitor" — out of scope for now.

---

## [SECTION] See also

- `08-our-pipeline.md` — the pipeline this change management plugs into
- `01-system/03-tools/check_traceability.py` — xlsx ↔ .feature key matching
- `01-system/01-skills/iterate-test-case-quality/SKILL.md` — the AI loop
- memory `reference_bdd_traceability_convention` — `@TAG` vs name-prefix
- memory `feedback_dont_refresh_pass_scenarios` — don't re-run Pass cases
  just to refresh xlsx (related anti-pattern)
