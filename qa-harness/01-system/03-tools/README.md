# 01-system/03-tools/

Harness contract tools. These scripts enforce consistency between xlsx test
cases, project `.feature` automation, and `dashboard.db` results.

## Gate

| Script | Purpose |
|---|---|
| `gate.py` | Chains the read-only validators below and returns PASS/FAIL for CI or local closeout. |

Default all-project check:

```powershell
python 01-system/03-tools/gate.py
```

For module/workstream closeout, keep the workbook explicit and scope
traceability to the matching case ID prefix:

```powershell
python 01-system/03-tools/gate.py `
  --xlsx "<path-to-active-workbook.xlsx>" `
  --case-prefix SIT-TC-WEB-AUTH-
```

## Validators

| Validator | Checks |
|---|---|
| `validate_testcase_xlsx.py` | xlsx schema, case ID format, required fields, status/priority enums, and yellow-row rule. |
| `check_traceability.py` | xlsx case IDs vs `.feature` scenarios vs dashboard history. |
| `validate_evidence.py` | Pass/Fail rows have Actual Result, Comments/Remarks, and embedded screenshot evidence. |
| `check_template_governance.py` | Templates are workflow-wired, gate-wired, and active instructions do not treat historical artifacts as template sources. |
| `check_requirement_review_interface.py` | Step 3.5 requirement consolidation uses the decision-only Chinese Q/U working interface, not legacy formal/internal headings. |
| `check_workflow_coverage.py` | Skills and templates are wired into `02-qa-workflow.md`. |
| `check_signoff_gate.py` | Step 3.5 gate: no test cases for a scope whose consolidation doc isn't Signed Off. |
| `check_testcase_review_gate.py` | Test-case review gate: matching `04-test-case-review/test-case-review-<scope>.md` must be signed, dated, and free of open comments before execution readiness. |
| `check_testcase_audit_trail.py` | Test-case change audit gate: add/modify/remove/scope-adjustment rows recorded in review docs must also be visible in workbook `Audit Trail`, and workbook audit rows must be present in the paired review DOCX. |

## Common Workflows

Just check traceability:

```powershell
python 01-system/03-tools/check_traceability.py `
  --xlsx "D:\Workspace\west-kowloon\01-requirements\**\test-cases-*.xlsx" `
  --features "D:\Workspace\west-kowloon\02-automation\01-features" `
  --db "D:\Workspace\qa-harness\02-platform\02-dashboard\01-backend\dashboard.db"
```

Check one case-ID family only:

```powershell
python 01-system/03-tools/check_traceability.py `
  --xlsx "<path-to-active-workbook.xlsx>" `
  --features "D:\Workspace\west-kowloon\02-automation\01-features" `
  --db "D:\Workspace\qa-harness\02-platform\02-dashboard\01-backend\dashboard.db" `
  --case-prefix SIT-TC-WEB-AUTH-
```

Write run results back to xlsx, dry-run first:

```powershell
python 01-system/03-tools/writeback_results.py `
  --xlsx "<path-to-active-workbook.xlsx>" `
  --from-db `
  --dry-run
```

Record a post-review or post-sign-off test-case change after the workbook has
already been updated:

```powershell
python 01-system/03-tools/record_testcase_change.py `
  --package "<requirement-package-path>" `
  --scope "<scope>" `
  --change-type scope-adjustment `
  --case-id SIT-TC-PROJ-MOD-001 `
  --actor "Test Manager / QA1 (AI)" `
  --reason "<why the case was added, modified, or removed>" `
  --scope-impact "<current scope impact and count>" `
  --evidence "03-test-design/CHANGE.md"
```

When a previous workbook is available, pass `--old-xlsx <previous.xlsx>` so the
tool can also mark added/modified case cells yellow with comments. Removed
cases are not present in the live workbook, so the workbook `Audit Trail` and
review `Review Trail` are the human-visible trace for removals.

## Writer

`writeback_results.py` and `record_testcase_change.py` are intentionally not
part of the gate because they write to workbooks. `writeback_results.py`
creates timestamped backups and never touches the Screenshots column.
`record_testcase_change.py` appends human-visible audit rows to current
workbooks and review documents, then re-renders review DOCX files.

## Package scanner

`package_scanner.py` walks every requirement package under a project's
`01-requirements/` and reports per-stage status (01-input through
07-release-feedback). Backs the dashboard's **Package Health** page; runnable
standalone for offline CLI inspection.

```powershell
python 01-system/03-tools/package_scanner.py                    # all west-kowloon packages, text output
python 01-system/03-tools/package_scanner.py --project west-kowloon --json
```

Per-stage status enum: `pass` | `partial` | `blocked` | `empty`. The
`blocked` status fires on `03-test-design` when a sibling
`02-analysis/requirement-consolidation-*.md` is not Signed Off
(consistent with `check_signoff_gate.py`). The `04-test-case-review` stage
uses `check_testcase_review_gate.py` logic, so a folder with files is not
enough: the matching review form must be signed, dated, and have
`Open Review Comments` set to `None`.

The scanner is presence-based + status-parse; it does NOT run validators
itself. The dashboard backend layers validator results on top via
separate endpoints (`/api/quality-system/packages/{id}/validate-xlsx`
and `/executions`).

## MD / DOCX hand-off converter

`md_docx.py` converts AI-drafted review artifacts (consolidation,
test case review, test report) between markdown (canonical, AI-readable)
and docx (human review derivative). See [`../12-md-docx-handoff.md`](../12-md-docx-handoff.md)
for the convention.

```powershell
# AI -> human: generate the .docx review copy alongside the canonical .md
python 01-system/03-tools/md_docx.py to-docx <path>\<artifact>.md

# Human reviewer edits the .docx (NOT the .md)

# Human -> AI: absorb edits back into canonical .md
python 01-system/03-tools/md_docx.py to-md <path>\<artifact>.docx

# Fidelity self-test on any md (informational)
python 01-system/03-tools/md_docx.py round-trip <path>\<artifact>.md
```

Backed by pandoc (bundled via `pypandoc-binary` in the venv — no
system install needed). Strips the UTF-8 BOM pandoc adds to converted
markdown (memory: `episode_codex_bom_auth_2026_05_28`).

`to-docx` fails fast when the source markdown contains raw HTML
`<table>` blocks because pandoc can drop or distort them. Convert those
tables to markdown table syntax before handoff. `--allow-raw-html-tables`
is only for legacy recovery, not normal review delivery.

## Requirement Review Interface Guard

`check_template_governance.py` is the general template authority guard:
canonical templates live in `01-system/02-templates`; dated historical
artifacts may be business references, but not runtime template sources.

```powershell
python 01-system/03-tools/check_template_governance.py
```

`check_requirement_review_interface.py` prevents old requirement-review
templates from leaking into new user-facing consolidation docs. It scans new
dated packages from 2026-07-15 onward plus the shared template and skill
instructions.

```powershell
python 01-system/03-tools/check_requirement_review_interface.py
```

The guard fails if a working consolidation doc uses `[SECTION]`,
`Integrated Breakdown`, `Hand-Off Statement`, `Review Findings`,
`Open Review Comments`, or other formal/internal fields instead of the fixed
Chinese Q/U decision table interface.
