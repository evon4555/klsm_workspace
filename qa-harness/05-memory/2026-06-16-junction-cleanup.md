# Junction Cleanup Decision

Date: 2026-06-16

Scope: `D:\Workspace`, `D:\Workspace\qa-harness`, `D:\Workspace\west-kowloon`

Decision:

- The workspace no longer uses `D:\qa-harness` or workspace-internal junctions.
- Active scripts, indexes, runbooks, and README files must point to numbered
  physical paths such as `01-system`, `02-platform\01-automation`, and
  `west-kowloon\02-automation`.
- Historical evidence may keep old absolute paths as historical facts, but
  normal work must not recreate compatibility aliases. Any future migration
  exception needs a dated note with owner, reason, and retirement condition.

Validation focus:

- Scan `D:\Workspace` for reparse points after structural edits.
- Run static smoke and targeted Python compile after path changes.
- Also self-test path-sensitive tools such as `gate.py`, `check_rule_drift.py`,
  and platform project-tool wrappers after removing aliases.
