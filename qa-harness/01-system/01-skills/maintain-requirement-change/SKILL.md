---
name: maintain-requirement-change
description: Use this skill when a requirement change package lands in `D:\Workspace\<project>\01-requirements\02-subprojects\<subproject>\02-modules\<module>\<yyyy-mm-dd>\` and the team needs to absorb it into test cases + automation without losing history. It chains diff_xlsx_versions → maintenance_scan → human review of report → cleanup (write new automation / soft-delete removed / fix drifted scenarios). The end state: every case in the new xlsx has a matching .feature scenario (or @na stub), and no stale automation lingers.
---

# Maintain Requirement Change

## Purpose

When PMs revise figma / PRD / mindmap and a new xlsx version is dropped,
this skill is the canonical "what now?" — it orchestrates the existing
tools so nothing gets forgotten between "requirement landed" and
"automation absorbed it."

This is the implementation skill behind `10-change-management.md`: the
policy doc says "use ISO dates, soft-delete, ID lineage, mandatory
CHANGE.md"; this skill is the runbook for **executing** that policy on
a specific change.

## When to use

- A new dated xlsx appears next to an existing one
  (`test-cases-<scope>_<YYYY-MM-DD>.xlsx` next to `test-cases-<scope>.xlsx`)
- A `CHANGE.md` was committed under the change package's `01-input/`
- The team asks "how do we update automation for this change?"

## When NOT to use

- First-time test case authoring (use `write-test-case`)
- Quality review of cases (use `review-test-case` or `iterate-test-case-quality`)
- Running existing tests (just run `behave` directly)

## Reference documents

- `../../10-change-management.md` — the policy this skill enforces
- `../../03-tools/diff_xlsx_versions.py` — semantic diff
- `../../03-tools/maintenance_scan.py` — wraps diff + cross-refs `02-automation/01-features/`
- `../iterate-test-case-quality/SKILL.md` — for the case-quality
  half of the cycle if the new xlsx was AI-drafted
- `../../02-templates/test-case-template.md` — schema for new rows
- memory `reference_bdd_traceability_convention` — how the matcher finds
  `01-features/` scenarios from case IDs

## Inputs

Required:

- Path to the **new** xlsx (`test-cases-<scope>_<YYYY-MM-DD>.xlsx`)
- Path to the **old** xlsx (auto-found by maintenance_scan via the same
  stem + earlier date, but pass explicitly if naming differs)

Strongly preferred:

- The CHANGE.md describing why / who / when / scope (per
  `10-change-management.md`). Without it, you can still execute but the
  audit trail loses the WHY.

## Workflow (4 phases)

```
        ┌─────────────────────────────────────────────────┐
        │  P1 DIFF                                        │
        │   diff_xlsx_versions.py OLD.xlsx NEW.xlsx       │
        │   --md diff_<date>.md                           │
        │  → see what changed (added / removed / modified)│
        └─────────────────────────────────────────────────┘
                            ↓
        ┌─────────────────────────────────────────────────┐
        │  P2 SCAN                                        │
        │   maintenance_scan.py NEW.xlsx                  │
        │  → maintenance_report.md with 4 TODO buckets:   │
        │    - write    (added, no .feature)              │
        │    - mod-unautomated (modified, no .feature)    │
        │    - drift    (modified, .feature exists)       │
        │    - deprecate (removed, .feature exists)       │
        └─────────────────────────────────────────────────┘
                            ↓
        ┌─────────────────────────────────────────────────┐
        │  P3 ACT (for each TODO bucket)                  │
        │   added/mod-unautomated → write new .feature    │
        │                           scenarios + step defs │
        │   drift                 → open scenario, compare│
        │                           step text vs new xlsx │
        │                           row, update where     │
        │                           needed                │
        │   deprecate             → maintenance_scan.py   │
        │                           --apply-deprecate     │
        │                           (or move by hand if   │
        │                           the file holds other  │
        │                           live scenarios)       │
        └─────────────────────────────────────────────────┘
                            ↓
        ┌─────────────────────────────────────────────────┐
        │  P4 VERIFY                                      │
        │   gate.py                                       │
        │  → must PASS before merging the change          │
        │   pytest 02-tests/api (smoke + contract)        │
        │  → must stay green                              │
        │   re-run maintenance_scan.py                    │
        │  → all 4 TODO counts → 0                        │
        └─────────────────────────────────────────────────┘
```

## Output

Per change, leave on disk:

```
D:\Workspace\<project>\01-requirements\02-subprojects\<subproject>\02-modules\<module>\<yyyy-mm-dd>\01-input\CHANGE.md
                                                  (already exists; you don't write this)

D:\Workspace\<project>\01-requirements\02-subprojects\<subproject>\02-modules\<module>\<yyyy-mm-dd>\03-test-design\
  ├── test-cases-<scope>_<YYYY-MM-DD>.xlsx         (the input)
  ├── diff_<YYYY-MM-DD>.md                         (P1 output)
  ├── diff_<YYYY-MM-DD>.json                       (P1 output)
  └── maintenance_report_<YYYY-MM-DD>.md           (P2 output)

D:\Workspace\<project>\02-automation\01-features\
  └── <module>_<scope>.feature                     (P3 output: new + modified)
       (or  01-features/deprecated/<YYYY-MM-DD>/   (P3 output: removed))
```

## Field guidance

### What counts as "drift" vs "mod-unautomated"

- **drift** — modified case + .feature scenario exists. Read the diff's
  `modified` section to see WHICH cells changed (steps? expected? scope?).
  Open the scenario, update only the steps that no longer match. Don't
  silently rewrite the whole scenario — drift implies an intentional
  re-author by humans.

- **mod-unautomated** — modified case but no .feature scenario yet.
  Same input as `added` for practical purposes: write fresh automation.
  Bucket it separately because it's a sign the test was DESIGN-ONLY
  before (never automated), so the new spec is the first real chance.

### Test case format/style continuity (High)

Before accepting a revised workbook, compare it with the previous approved
version. Added and modified cases must follow the previous version's row style:
same step numbering, same expected-result granularity, same enum/priority
labels, same owner/environment style, and same use of bold diff markers. If
the only reason for the difference is "another AI/model wrote this version",
normalize it before closeout.

Do not mix concise rows with narrative rows inside one workbook. A format
migration is allowed only when explicitly recorded in `CHANGE.md` / Revision
History and applied consistently to the whole workbook.

### When to leave an item as @na rather than write automation

- Case description has "TBD" / "Deferred" / "Pending PM" markers
- Case targets a feature not yet in the deployed SIT environment (set
  `@needs-oauth-mock` or similar gating tag — see
  `D:\Workspace\west-kowloon\02-automation\01-features\ui_e2e\antank_third_party_login.feature` for the pattern)
- Case is HK / mobile / env-specific and the harness can't drive it

Document the @na reason in the scenario's `Given` step skip message —
that text shows up in the dashboard "Skipped" tooltip.

### Soft-delete vs hard-delete

Per `10-change-management.md`: **soft-delete first**. Move the .feature
file (or just its scenarios) into `02-automation/01-features/deprecated/<date>/`
and keep for 1-2 sprints. Only hard-delete after no rollback has
happened in that window. The `--apply-deprecate` flag does this safely
for file-level moves; scenario-level moves are manual today.

### ID lineage

When a case is `modified`, **keep the same ID**. Add `last_revised:
2026-06-02` to the case row if the schema supports it (today it doesn't;
in CHANGE.md is fine). Renumbering breaks dashboard trend continuity.

## Reflexion checklist before declaring done

- [ ] gate.py OVERALL: PASS
- [ ] maintenance_scan.py final run: write=0, deprecate=0, drift=0,
      mod-unautomated=0
- [ ] For v2+ work, added/modified test cases match the previous approved
      version's format and writing style
- [ ] CHANGE.md is filled (Why / Source / Approver / Effective / Scope)
- [ ] Added/modified/removed cases are recorded in workbook `Audit Trail`
      sheet(s) and paired review DOCX `Review Trail and Version Record`
      rows by running `01-system/03-tools/record_testcase_change.py`
- [ ] Every `added` case has a real or @na scenario in features/
- [ ] Every `removed` case's scenario moved to deprecated/ (not hard-deleted)
- [ ] Every `modified` case's scenario re-read by a human (drift mode is
      easy to get wrong silently)
- [ ] If you used --apply-deprecate, confirm no live scenarios were
      collateral-damaged (one .feature file can hold multiple scenarios)

## Worked example

See the 2026-06-02 change set:

```
D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\01-login-registration\2026-06-16\
├── 01-input/figma/2026-06-02/CHANGE.md
└── 03-test-design/
    ├── test-cases-registration-login_2026-06-02.xlsx
    ├── diff_2026-06-02.md
    └── maintenance_report_2026-06-02.md

D:\Workspace\west-kowloon\02-automation\01-features\ui_e2e\antank_third_party_login.feature    ← P3 output
```

Numbers: 7 modified + 10 added cases → 17 new scenarios written +
21 unrelated `@na` stubs added for 1:1 traceability.
