# Memory

This folder stores durable working memory for the QA harness.

Use it for decisions that should survive chat context loss:

- architecture decisions
- project conventions
- feedback that should affect future work
- rule-promotion decisions
- migration notes
- repeated mistakes to avoid

Do not use memory as a dumping ground. A memory entry should be short,
actionable, dated, and linked to the files it affects.

Imported Claude memory is preserved under `claude-import\`. Treat those files
as source material. Promote only current, useful decisions into top-level dated
memory files, `docs`, or `system`.

## Memory Rules

1. Store durable rules on disk, not only in chat.
2. Separate stable rules from temporary observations.
3. Include the scope: system-wide, project-specific, or session-only.
4. Include the date and reason.
5. Retire or replace stale entries when the project changes.
6. Promote project lessons into `qa-system` only when they are reusable.
7. Keep important workspace memory LLM-neutral: Codex, Claude Code, and other
   agents must be able to recover the same rule from visible files under
   `D:\Workspace`.

## Naming

Use:

```text
YYYY-MM-DD-short-topic.md
```

Examples:

```text
2026-06-06-workspace-refactor.md
2026-06-15-westk-otp-rule-promoted.md
```
