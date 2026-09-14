# West Kowloon Project Workspace

This folder is the project-level workspace for the West Kowloon Ticketing and
Admission work. It consumes the shared QA harness from
`D:\Workspace\qa-harness` and keeps West Kowloon-specific material out of the
shared system.

## Primary Structure

Use the numbered folders for new work:

```text
west-kowloon\
  01-requirements\  project facts, subprojects, modules, changes, test design
  02-automation\    project-specific features, steps, page objects, tests, tools
  03-evidence\      durable execution evidence and delivery proof
```

The numbered folders are physical directories. The old unnumbered compatibility
paths (`requirements`, `automation`, `evidence`, `Website`, `BoxOffice`) have
been retired and should not be used for new work.

## AI Agent Entry Points

- Codex: `CODEX.md`
- Claude Code: `CLAUDE.md`
- Other agents: `AGENTS.md`

Project-owned AI skills live under
`01-requirements\00-project-overview\project-ai-skills`; user-local agent
skills are launchers only.

## Project Layout

```text
01-requirements\
  00-project-overview\
  01-source-documents\
  02-subprojects\
    01-box-office\
    02-website\
      01-source-documents\
      02-modules\
        01-login-registration\
        02-homepage\
        03-ticketing\
        04-seat-selection\
        05-membership-card\
        06-events\
        07-merchandise\
```

Website source PRDs are rolling full-website inputs under
`01-requirements\02-subprojects\02-website\01-source-documents`. Module folders under `01-requirements\02-subprojects\02-website\02-modules`
are the derived working views for analysis, test design, review, and execution.
Use direct dated folders under each module for Website requirement-change
packages, for example `01-requirements\02-subprojects\02-website\02-modules\01-login-registration\2026-06-23`.

## Context Layers

Use the narrowest reliable context first:

1. Requirement or change context:
   `D:\Workspace\west-kowloon\01-requirements\02-subprojects\<subproject>\02-modules\<module>\<yyyy-mm-dd>`
2. Subproject context:
   `D:\Workspace\west-kowloon\01-requirements\02-subprojects\<subproject>`
3. Project context:
   `D:\Workspace\west-kowloon\01-requirements`
4. Company context:
   `D:\Workspace\qa-harness\03-context\company`
5. Shared QA system:
   `D:\Workspace\qa-harness\01-system`

Requirement-specific facts override project assumptions. Project facts override
company background. Shared harness rules apply unless the project records a
deliberate exception.

## Automation Layout

Current status: the automation folder contains useful historical assets, but
older scripts and flows are not the current quality baseline. Treat them as
legacy material until they are reviewed and cleaned. For new requirement and
test-case work, update `01-requirements` first; only reuse automation scripts
after confirming they still match the latest UI/API.

Use the numbered automation view for new work:

```text
02-automation\
  01-features\
    api_ui_mixed\
    ui_e2e\
  02-tests\
    api\
      api_smoke\
      api_contract\
      api_functional\
      api_ui_mixed\
    performance\
  03-src\
    test_automation\
      web\      page objects and browser UI helpers
      flows\    reusable business flow runners
  04-tools\
  05-config\
  06-envs\
  07-artifacts\
```

Reusable runners, framework primitives, dashboard integration, and platform
strategy stay in `D:\Workspace\qa-harness\02-platform\01-automation`.

## Evidence Layout

Use `03-evidence` for project execution evidence that is not part of the
reusable QA harness, such as:

- manual execution records
- automation run exports selected for review
- screenshots and logs
- defect triage exports
- release or delivery proof

Generated automation artifacts may remain under `02-automation\07-artifacts`
while a run is active. Promote durable evidence into `03-evidence` when it
needs to be reviewed or preserved outside the automation runtime.

## Path Rule

Use numbered folders directly. Do not create or depend on project-root aliases
for modules or changes. If historical evidence mentions an old path, leave it
as history or add a migration note; do not point active indexes back to retired
paths.

## Current Source Baseline

The current project context is mainly derived from:

- `01-requirements\01-source-documents\01-it-pmo\IT-PMO-410-Requirement-Document_V1.0.pdf`
- `01-requirements\01-source-documents\01-it-pmo\IT-PMO-420-Functional-Specification-Document_V1.0_0414.docx`
- `01-requirements\01-source-documents\02-templates\TestCase_Template.xlsx`
