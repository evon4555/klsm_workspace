# Workspace

This workspace separates the reusable QA harness from concrete project work.

```text
D:\Workspace\
  qa-harness\       shared QA harness and execution platform view
  standard product\ SaaS baseline product workspace
  west-kowloon\     West Kowloon customer project workspace
  jockey club\      Jockey Club customer project workspace
```

The top-level project names stay stable. Inside each workspace entry, use the
numbered folders for day-to-day work.

## Working Rule

For current solo work, `D:\Workspace` does not require every project folder to
be a git repository. Keep work safe by using dated source-document folders,
versioned deliverable filenames, and short index notes that say which version is
current.

Before broad folder restructures or bulk deletes, make a temporary copy or
archive of the affected project folder. Add git later when any of these become
true:

- more than one person edits the same project workspace
- changes need review before delivery
- exact rollback history matters
- a client or team needs a commit-level audit trail

## How To Read This Workspace

- Start with `qa-harness` when you need standards, templates, AI skills,
  validators, platform runbooks, dashboard, automation strategy, or infra.
- Start with `standard product` when you are working on baseline SaaS product
  requirements, admin-backend capability, shared product behavior, or reusable
  product decisions.
- Start with `west-kowloon` when you are working on the West Kowloon project,
  its requirements, automation assets, or evidence.
- Start with `jockey club` when you are working on the Jockey Club project,
  its customer-specific requirements, automation assets, or evidence.

West Kowloon and Jockey Club are customer project workspaces. Their behavior
should be interpreted as extensions or overrides on top of `standard product`
unless a project requirement explicitly says otherwise.

The workspace is now the human-facing structure. The old root-level
compatibility junction has been retired; use `D:\Workspace\qa-harness`.

## AI Agent Entry Points

This workspace is LLM-neutral. Codex, Claude Code, and other agents should read
the same visible workspace files instead of depending on one assistant's hidden
or user-local memory.

- General agents: `AGENTS.md`
- Codex: `CODEX.md`
- Claude Code: `CLAUDE.md`

Durable rules, project skills, templates, and review decisions should live under
`D:\Workspace`. User-local agent folders are launchers or convenience copies
only.

## Current Layout

```text
D:\Workspace\
  qa-harness\
    01-system\
    02-platform\
      01-automation\
      02-dashboard\
      03-infra\
    03-context\
    04-docs\
    05-memory\
    06-artifacts\
  west-kowloon\
    01-requirements\
    02-automation\
    03-evidence\
  standard product\
    01-requirements\
    02-automation\
    03-evidence\
  jockey club\
    01-requirements\
    02-automation\
    03-evidence\
```

Each concrete project should follow this shape:

```text
project-x\
  01-requirements\  project requirements, changes, source documents, test design
  02-automation\    project-specific automation assets
  03-evidence\      project-specific execution evidence
```

## Optional Shell Setup

For a PowerShell session that should use the compatibility conventions:

```powershell
.\set-workspace-env.ps1
```

This sets `QA_WORKSPACE_ROOT`, `QA_HARNESS_ROOT`, `QA_STANDARD_PRODUCT_ROOT`,
`QA_WESTK_ROOT`, and `QA_JOCKEY_CLUB_ROOT` for the current shell only.
`QA_HARNESS_ROOT` points to `D:\Workspace\qa-harness`.

## No Junction Rule

The numbered folders are physical directories, not junction aliases. The old
root-level `D:\qa-harness` path and the workspace-internal compatibility
junctions have been retired.

Use these roots for new commands and documentation:

```text
QA_WORKSPACE_ROOT=D:\Workspace
QA_HARNESS_ROOT=D:\Workspace\qa-harness
QA_STANDARD_PRODUCT_ROOT=D:\Workspace\standard product
QA_WESTK_ROOT=D:\Workspace\west-kowloon
QA_JOCKEY_CLUB_ROOT=D:\Workspace\jockey club
```

Preserve old absolute paths only inside historical evidence or dated migration
notes. Active scripts, indexes, and runbooks should point to the numbered
workspace paths above.
