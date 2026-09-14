# Workspace Refactor Memory

Date: 2026-06-06
Scope: system-wide workspace structure

## Decision

Use `D:\Workspace` as the human-facing workspace root.

The first-level model is:

```text
D:\Workspace\
  qa-harness\
  west-kowloon\
  project-2\
  project-3\
```

`qa-harness` is the reusable QA thinking system. Concrete project output should
live in project workspaces and follow the harness.

## Why

The old `D:\qa-harness` tree mixed shared standards, West Kowloon project
artifacts, automation, dashboard, infrastructure, company documents, and
requirement history. That made the harness look like one project folder instead
of a reusable operating model.

## Applied Now

A non-destructive junction view was created:

- `D:\Workspace\qa-harness\system` -> `D:\qa-harness\qa-system`
- `D:\Workspace\qa-harness\context\company` -> `D:\qa-harness\company`
- `D:\Workspace\qa-harness\platform\automation` -> `D:\qa-harness\automation`
- `D:\Workspace\qa-harness\platform\dashboard` -> `D:\qa-harness\dashboard`
- `D:\Workspace\qa-harness\platform\infra` -> `D:\qa-harness\infra`
- `D:\Workspace\west-kowloon` -> `D:\qa-harness\requirements\西九`

No original source directories were moved in this phase.

## Memory Principle

Do not rely on chat context as the only place where project decisions live.
Following the ChatGPT memory/dreaming idea of synthesising useful context over
time, this harness keeps durable working memory as small dated files under
`memory\`.

Reference: https://openai.com/index/chatgpt-memory-dreaming/

## Future Rule

When a project reveals a reusable lesson, first write it under the project
rules area. Promote it to `qa-harness/system` only after the rule-promotion
policy confirms it is reusable.

## Related Files

- `docs/workspace-structure.md`
- `qa-system/11-rule-promotion.md`
- `qa-system/10-change-management.md`
- `qa-system/02-qa-workflow.md`
