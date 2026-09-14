# Template Governance Guard

Date: 2026-07-15

Trigger: the user clarified that no future work should repeatedly index a
specific historical artifact as a template. Good historical formats must be
extracted into the canonical template instead.

Decision: all reusable QA templates are governed from
`D:\Workspace\qa-harness\01-system\02-templates`. Active instructions must not
tell agents to use a dated historical package as a template source.

Guard: `D:\Workspace\qa-harness\01-system\03-tools\check_template_governance.py`
checks template workflow wiring, gate wiring, and active instruction surfaces
for historical-artifact-as-template regressions.

Scope: applies to future template, skill, and workflow edits under
`D:\Workspace`.
