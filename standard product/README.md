# Standard Product Workspace

This folder is the baseline SaaS product workspace. Customer project
workspaces such as `D:\Workspace\west-kowloon` and
`D:\Workspace\jockey club` are created from this product baseline and then
extended by project-specific requirements.

## Primary Structure

Use the numbered folders for new work:

```text
standard product\
  01-requirements\  baseline product requirements and shared product decisions
  02-automation\    baseline product automation assets
  03-evidence\      baseline product evidence and delivery proof
```

## Current Requirement Index

Current baseline product requirement workstreams:

| Area | Path | Status |
|---|---|---|
| Domestic projects | `01-requirements\02-subprojects\01-domestic projects` | Active; contains ticketing modules and current configuration work. |
| Overseas projects | `01-requirements\02-subprojects\02-overseas projects` | Placeholder; no active requirement package indexed yet. |

Current active package:

- `01-requirements\02-subprojects\01-domestic projects\02-modules\04-Configuration Related\2026-07-15` - batch session configuration from ZenTao story 4086.

## Scope Rule

Put behavior here only when it belongs to the reusable product baseline.
Customer-specific behavior belongs in the relevant customer project workspace.

## AI Agent Entry Points

- General agents: `AGENTS.md`
- Codex: `CODEX.md`
- Claude Code: `CLAUDE.md`

## Context Order

Use context in this order:

1. Current requirement package
2. Standard product project context
3. Shared company context under `D:\Workspace\qa-harness\03-context`
4. Shared QA system under `D:\Workspace\qa-harness\01-system`
