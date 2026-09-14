# West Kowloon Project AI Skills

This folder is the project-owned source of truth for West Kowloon AI workflow
skills. User-local agent folders such as `C:\Users\klsm\.codex\skills` should
only point here; they must not become the only copy of project rules.

## Index

| Skill | Purpose |
|---|---|
| `westk-testcase-workflow/SKILL.md` | Test case generation, QA2 review, revision, workbook regeneration, and ticket-type split routing. |
| `westk-review-signoff/SKILL.md` | Human review comments, Review Trail, formal DOCX rendering, and Test Manager sign-off sync. |
| `westk-zh-en-translation/SKILL.md` | Chinese-to-English translation style for West Kowloon QA artifacts. |

## Cross-Agent Rule

When working in this project with Codex, Claude Code, or another AI agent:

1. Read the matching project skill here first.
2. Read the referenced harness skill under
   `D:\Workspace\qa-harness\01-system\01-skills`.
3. Read project context and indexes under
   `D:\Workspace\west-kowloon\01-requirements\00-project-overview`.
4. Treat user-local skills as launchers or shortcuts only.

## Entry Files

- Codex: `D:\Workspace\west-kowloon\CODEX.md`
- Claude Code: `D:\Workspace\west-kowloon\CLAUDE.md`
- Other agents: `D:\Workspace\west-kowloon\AGENTS.md`

## Validation

Run these checks after changing project skills or related rules:

```powershell
python D:\Workspace\qa-harness\01-system\03-tools\check_workflow_coverage.py
python D:\Workspace\qa-harness\01-system\03-tools\check_rule_drift.py --requirements-dir D:\Workspace
```
