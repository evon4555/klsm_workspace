# Workspace Agent Instructions

This workspace is the durable source of truth for QA rules, project context,
skills, templates, review decisions, and memory. Do not rely on one LLM's hidden
chat memory or user-local private folder as the only copy of an important rule.

## Start Here

1. Read this file.
2. Read `D:\Workspace\README.md`.
3. Select the active project or harness area:
   - Shared QA system: `D:\Workspace\qa-harness`
   - Standard product baseline: `D:\Workspace\standard product`
   - West Kowloon project: `D:\Workspace\west-kowloon`
   - Jockey Club project: `D:\Workspace\jockey club`
4. Read the selected folder's agent entry file before editing artifacts:
   - `AGENTS.md` for general agents
   - `CODEX.md` for Codex
   - `CLAUDE.md` for Claude Code

## Durable Memory Rule

When a rule, workflow, template decision, migration decision, or repeated user
correction should survive model switching, record it in visible workspace files.
Use one of these durable locations:

- shared reusable QA rules: `D:\Workspace\qa-harness\01-system`
- shared dated memory: `D:\Workspace\qa-harness\05-memory`
- project-owned rules and context: each project's `01-requirements`
- project AI skills: each project's project-owned skill folder, such as
  `D:\Workspace\west-kowloon\01-requirements\00-project-overview\project-ai-skills`

## SaaS Product Line Rule

`D:\Workspace\standard product` is the baseline product workspace. Customer
projects such as `D:\Workspace\west-kowloon` and `D:\Workspace\jockey club`
are created from the standard product and then extended by project-specific
requirements.

When customer requirements are incomplete, read the customer project first,
then use the standard product as the baseline. Do not copy customer-specific
rules back into the standard product unless the user explicitly confirms that
the behavior is product-wide.

User-local folders such as `C:\Users\klsm\.codex\skills` or assistant-specific
memory folders may be launchers, caches, or convenience copies only. They must
not be the only place where important project knowledge exists.

## Cross-LLM Portability

Codex, Claude Code, and other LLM agents should reach the same rules by reading
the project-owned files under `D:\Workspace`. If an agent-local skill or memory
conflicts with the visible workspace files, the visible workspace files win.

## Sensitive Data

Do not store secrets, passwords, API keys, cookies, tokens, private auth
payloads, or raw credential files in memory notes or project rules.
