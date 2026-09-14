# Jockey Club Project Workspace

This folder is the customer project workspace for Jockey Club. It is created
from the SaaS baseline in `D:\Workspace\standard product` and should record
Jockey Club-specific requirements, automation assets, and evidence.

## Primary Structure

Use the numbered folders for new work:

```text
jockey club\
  01-requirements\  project requirements, changes, source documents, test design
  02-automation\    project-specific automation assets
  03-evidence\      project-specific execution evidence
```

## Baseline Rule

Start from `D:\Workspace\standard product` when a requirement depends on
baseline product behavior. Record only Jockey Club-specific deltas here.

## AI Agent Entry Points

- General agents: `AGENTS.md`
- Codex: `CODEX.md`
- Claude Code: `CLAUDE.md`

## Context Order

Use context in this order:

1. Current requirement package
2. Jockey Club project context
3. Standard product baseline context
4. Shared company context under `D:\Workspace\qa-harness\03-context`
5. Shared QA system under `D:\Workspace\qa-harness\01-system`
