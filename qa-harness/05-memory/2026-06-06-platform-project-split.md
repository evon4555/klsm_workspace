# Platform Project Split Memory

Date: 2026-06-06
Scope: workspace structure and automation ownership

## Decision

West Kowloon-specific automation assets now live under:

```text
D:\Workspace\west-kowloon\automation
```

The reusable harness automation platform remains under:

```text
D:\Workspace\qa-harness\platform\automation
```

## Compatibility

The platform keeps junctions for project-owned folders so existing commands
continue to work:

```text
features
tests\api
src\test_automation\web
config
envs
artifacts
```

The legacy root remains valid:

```text
D:\qa-harness\automation -> D:\Workspace\qa-harness\platform\automation
```

## Next Rule

Do not split `platform\automation\tools` until each tool is classified as
project-specific or reusable and each moved command has a wrapper or documented
compatibility path.

Durable memory should stay short, dated, reviewable, and current. Project facts
start in the project workspace; only reusable lessons should be promoted into
the harness system.
