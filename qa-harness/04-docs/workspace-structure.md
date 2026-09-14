# Workspace Structure Refactor

Date: 2026-06-06

## Intent

The pre-workspace harness tree mixed several concepts:

- shared QA methodology
- project-specific outputs
- company background
- automation code
- dashboard and observability infrastructure
- historical requirement-change packages

The target mental model is workspace-first:

```text
D:\Workspace\
  qa-harness\       shared QA harness, standards, templates, skills, validators
  west-kowloon\     current West Kowloon project workspace
  project-2\        future project workspace
  project-3\        future project workspace
```

`qa-harness` should be the system of thinking and governance. Projects should
consume it, follow it, and feed reusable lessons back into it.

## Phase 1 Implemented

This phase created a low-risk workspace view using Windows junctions. The old
root-level compatibility path was kept temporarily for scripts that still
hard-coded it.

```text
D:\Workspace\
  README.md
  qa-harness\
    README.md
    system\                 physical QA system workspace
    docs\
    memory\
    context\
      company\
    platform\
      automation\
      dashboard\
      infra\
  west-kowloon\             physical project workspace
```

Legacy compatibility path during migration:

```text
<old-root>\requirements\西九 -> D:\Workspace\west-kowloon
```

## Phase 2 Implemented

This phase reduced runtime dependence on the old absolute path while still
keeping the root-level compatibility entry alive as the physical repo root.

Path convention:

```text
QA_WORKSPACE_ROOT=D:\Workspace
QA_HARNESS_ROOT=<qa-harness repo root>
QA_WESTK_ROOT=<west-kowloon project root>
QA_GRAFANA_DASHBOARDS=<qa-harness>\02-platform\03-infra\03-grafana\dashboards
```

Changes made:

- startup scripts now derive the repo root from script location, with
  `QA_HARNESS_ROOT` as an override
- Python tools now derive repo/project roots instead of hard-coding the install
  drive
- Grafana provisioning is routed through environment variables set by
  `infra\start-grafana.bat`
- the workspace view now exposes `docs\` and `memory\` as first-class harness
  areas
- historical Markdown, feature files, and ZenTao delivery text were not bulk
  rewritten

## Phase 3 Implemented

West Kowloon has been physically extracted:

```text
D:\Workspace\west-kowloon
```

During migration, the old repo path remained available as a junction:

```text
<old-root>\requirements\西九 -> D:\Workspace\west-kowloon
```

This gives the workspace the intended first-level shape while preserving
existing scripts, historical paths, and validators that still read through the
legacy project path.

## Phase 4 Implemented

The reusable QA system has been physically extracted:

```text
D:\Workspace\qa-harness\01-system
```

During migration, the old repo path remained available as a junction:

```text
<old-root>\qa-system -> D:\Workspace\qa-harness\01-system
```

Before the move, `qa-system/tools/_paths.py` and dependent tools were updated
so gates can still resolve the physical checkout from either the old command
path or the workspace entry with `QA_HARNESS_ROOT` set.

## Conceptual Boundaries

### qa-harness/system

Shared and project-neutral:

- quality principles
- workflow
- roles
- gates
- evidence rules
- metrics
- source authority model
- templates
- AI skills
- validators and gates
- rule promotion policy

This is the part that should become stronger as projects generate feedback.

### qa-harness/context/company

Shared context used across projects, but not a QA standard by itself:

- company domain terms
- company background
- common business risk vocabulary

It supports projects, but it should not override project or requirement facts.

### qa-harness/platform

Reusable execution platform:

- BDD and Playwright automation framework
- dashboard
- observability stack
- smoke scripts
- runbooks

This area still contains West Kowloon / Antank-specific implementation details.
Future cleanup should separate generic framework code from project-specific
features, page objects, accounts, and evidence.

### west-kowloon

Project workspace:

- project overview
- project rules
- source documents
- Website workstream
- requirement-change packages
- test strategies
- test cases
- reviews
- execution records
- release notes

Project-specific rules should start here. They should be promoted to
`qa-harness/system` only after the rule-promotion policy says they are reusable.

## What Not To Do

- Do not keep adding new project folders under `qa-harness/system`.
- Do not put a project-specific pipeline into the shared harness as if it were
  universal.
- Do not overwrite requirement packages when requirements change. Version,
  diff, and keep an audit trail.
- Do not treat AI memory as hidden state only. Durable decisions should be
  written to disk.
- Do not silently rewrite historical evidence paths. Add a migration note
  instead.

## Phase 5 Implemented

Most remaining harness areas were converted from workspace junctions into
physical workspace directories:

```text
D:\Workspace\qa-harness\03-context\company
D:\Workspace\qa-harness\04-docs
D:\Workspace\qa-harness\05-memory
D:\Workspace\qa-harness\02-platform\01-automation
D:\Workspace\qa-harness\02-platform\02-dashboard
D:\Workspace\qa-harness\02-platform\03-infra
D:\Workspace\qa-harness\06-artifacts
```

The old root-level entries pointed back to those workspace directories as
compatibility junctions during migration.

## Phase 6 Implemented

West Kowloon-specific automation assets were moved under the project workspace:

```text
D:\Workspace\west-kowloon\02-automation
```

The project automation assets are physical project-owned directories:

```text
D:\Workspace\west-kowloon\02-automation\01-features
D:\Workspace\west-kowloon\02-automation\02-tests
D:\Workspace\west-kowloon\02-automation\03-src
D:\Workspace\west-kowloon\02-automation\04-tools
D:\Workspace\west-kowloon\02-automation\05-config
D:\Workspace\west-kowloon\02-automation\06-envs
D:\Workspace\west-kowloon\02-automation\07-artifacts
```

See `docs\platform-project-split.md`.

## Phase 7 Implemented

The West Kowloon project workspace now follows the project contract directly:

```text
D:\Workspace\west-kowloon\
  01-requirements\
    00-project-overview\
    01-source-documents\
    02-subprojects\
  02-automation\
  03-evidence\
```

The old project-root entries have been retired. New project work should use:

```text
project-x\
  01-requirements\  project requirements, changes, source documents, test design
  02-automation\    project-specific automation assets
  03-evidence\      project-specific execution evidence
```

## Phase 8 Implemented

Human-facing architecture folders now expose numbered physical directories.
Old compatibility entries have been retired.

Harness view:

```text
D:\Workspace\qa-harness\
  01-system\
  02-platform\
    01-automation\
    02-dashboard\
    03-infra\
      01-prometheus\
      02-loki\
      03-grafana\
  03-context\
  04-docs\
  05-memory\
  06-artifacts\
```

Project view:

```text
D:\Workspace\west-kowloon\
  01-requirements\
  02-automation\
  03-evidence\
```

West Kowloon requirements now expose subproject and module structure:

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

Website requirement-change outputs now live directly under the affected module
by source/change date:

```text
02-modules\<module>\<yyyy-mm-dd>
```

The old unnumbered folders are hidden, not deleted. They keep scripts and
  historical paths working while the visible workspace sorts consistently.
  The root-level compatibility entry has since been retired.

Claude Markdown memory was also imported into:

```text
D:\Workspace\qa-harness\05-memory\claude-import
```

## Phase 9 Implemented

The root-level and workspace-internal compatibility junctions have been
physically retired. The current workspace uses physical numbered directories:

```text
D:\Workspace\qa-harness\
  01-system\
  02-platform\
    01-automation\
    02-dashboard\
    03-infra\
  03-context\
  04-docs\
  05-memory\
  06-artifacts\

D:\Workspace\west-kowloon\
  01-requirements\
  02-automation\
  03-evidence\
```

Do not recreate `D:\qa-harness` or workspace-internal junction aliases for
normal work. Historical evidence may still mention old paths; active scripts,
indexes, and runbooks should point to the numbered physical paths.

## Later Cleanup

The physical structure is now in place. Remaining cleanup should be smaller and
semantic, not another broad directory move.

Recommended sequence:

1. Keep `QA_HARNESS_ROOT` and `QA_WESTK_ROOT` working during the transition.
2. Decide whether historical evidence paths should stay as legacy references
   or receive a migration note.
3. Split `02-platform\01-automation\03-tools` into reusable tools and project delivery
   tools after wrapper/link behavior is explicit.
4. Promote only reusable West Kowloon lessons into `qa-harness\system`.
5. Keep legacy paths only in historical evidence or migration notes; do not
   keep them available through junction aliases.

## Verification

- `02-platform\01-automation\03-tools\smoke_docs.py`
- `02-platform\01-automation\03-tools\smoke_dashboard.py`
- `01-system\03-tools\gate.py`
- grep for old absolute paths:

```powershell
rg -n "D:\\qa-harness|qa-system/|automation/|dashboard/" D:\Workspace\qa-harness -g "*.md" -g "*.py" -g "*.js" -g "*.ps1" -g "*.bat"
```

Current old absolute-path references are no longer in startup scripts, batch
files, PowerShell scripts, Grafana config, or runtime defaults. Remaining
references are mainly historical project artifacts and ZenTao delivery text.

See also:

- `docs\historical-path-policy.md`
- `docs\migration-gates.md`
