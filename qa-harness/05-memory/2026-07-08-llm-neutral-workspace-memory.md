# 2026-07-08 LLM-Neutral Workspace Memory

Scope: `D:\Workspace` and all project workspaces under it.

Decision: Important QA rules, workflow decisions, project skills, templates,
review/sign-off rules, and repeated user corrections must live in visible
workspace files under `D:\Workspace`, not only in Codex, Claude Code, or another
LLM's private local memory.

Reason: The user wants to switch between different LLMs at any time without
losing project memory or changing the effective workflow.

Implementation:

- Workspace entry files: `D:\Workspace\AGENTS.md`, `D:\Workspace\CODEX.md`,
  and `D:\Workspace\CLAUDE.md`.
- Project entry files should point back to project-owned rules and skills.
- User-local agent folders are launchers or convenience copies only.
- If assistant-local memory conflicts with workspace files, workspace files win.
