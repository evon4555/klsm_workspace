# QA Harness Workspace View

This folder is the clean workspace entry for the QA harness.

Use the numbered folders for new work:

```text
qa-harness\
  01-system\      reusable QA standards, templates, skills, validators
  02-platform\    automation strategy/runtime, dashboard, and infra
  03-context\     shared company context used by projects
  04-docs\        migration and architecture notes
  05-memory\      durable dated working memory
  06-artifacts\   generated reports and harness run outputs
```

The numbered folders are the physical working structure. Do not rely on old
unnumbered aliases such as `automation`, `dashboard`, `infra`, `qa-system`, or
`system`; those compatibility paths have been retired.

## Platform Layout

```text
02-platform\
  01-automation\
  02-dashboard\
  03-infra\
```

`03-infra` keeps Prometheus, Loki, and Grafana as platform infrastructure. They
are not QA standards, so they do not belong under `01-system`.

## Commands

From this folder:

```powershell
.\gate.ps1
.\smoke-docs.ps1
.\start-all.bat
.\stop-all.bat
```

## Read First

- `01-system\README.md`
- `01-system\02-qa-workflow.md`
- `01-system\04-quality-gates.md`
- `01-system\05-evidence-standard.md`
- `01-system\11-rule-promotion.md`
- `04-docs\project-workspace-contract.md`

## AI Agent Entry Points

- General agents: `AGENTS.md`
- Codex: `CODEX.md`
- Claude Code: `CLAUDE.md`

Harness rules are LLM-neutral. Assistant-local folders can point here, but
current standards and durable memory should remain visible under
`D:\Workspace\qa-harness`.

## Project Entry

Current project:

- `D:\Workspace\west-kowloon`

Project-specific automation lives under:

- `D:\Workspace\west-kowloon\02-automation`

Project-specific automation lives in the project workspace. The harness only
keeps reusable platform code and entry scripts.
