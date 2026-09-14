# 2026-07-18 Execution Audit And Evidence Rules

Scope: all D:\Workspace QA harness projects, especially Behave-first automation after test-case review sign-off.

Trigger: Standard Product Batch Session Configuration exposed gaps where removed cases, stale run summaries, mixed evidence, and workbook audit trail could drift.

Rules:

- Post-sign-off case add/modify/remove decisions must be visible in the current `.xlsx` `Audit Trail` and the paired human review `.docx` review trail. MD-only audit notes are not enough.
- Removed cases must be excluded from current `.xlsx`, live `.feature`, layer summaries, latest execution snapshots, and dashboard current scope. Historical DB rows and deprecated feature files may retain them only as superseded audit evidence.
- API write/update evidence must prove transition: setup a different precondition value, write the target value, then read back and show `before_matched_target=false` and `changed_from_before=true`.
- Mixed automation uses API for setup/action/non-checkpoint work and Playwright only for the final user-facing checkpoint. Evidence must include one API summary and one final UI assertion screenshot registered to the same case.
- Execution review must cite the package-local fixed MD/JSON snapshot under `05-execution/04-execution-results`, not only the live dashboard. Older runs stay in review trail as `Superseded`.
- Before declaring execution done, run targeted `gate.py` against the current workbook, feature root, dashboard DB, and case prefix; a DB warning for removed historical cases is acceptable only when current xlsx/features/latest snapshot exclude them.
