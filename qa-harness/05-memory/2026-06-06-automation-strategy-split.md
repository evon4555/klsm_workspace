# Automation Strategy Split Memory

Date: 2026-06-06
Scope: automation platform and project ownership

## Decision

`qa-harness\platform\automation` is the reusable automation strategy and runtime
layer. Project-specific automation assets belong under each project.

West Kowloon now owns:

```text
D:\Workspace\west-kowloon\automation\features
D:\Workspace\west-kowloon\automation\src\test_automation\web
D:\Workspace\west-kowloon\automation\tests\api
D:\Workspace\west-kowloon\automation\tests\performance
D:\Workspace\west-kowloon\automation\tools
D:\Workspace\west-kowloon\automation\config
D:\Workspace\west-kowloon\automation\envs
D:\Workspace\west-kowloon\automation\artifacts
```

The platform owns:

```text
D:\Workspace\qa-harness\platform\automation\strategy
D:\Workspace\qa-harness\platform\automation\src\test_automation
D:\Workspace\qa-harness\platform\automation\tools\smoke_dashboard.py
D:\Workspace\qa-harness\platform\automation\tools\smoke_docs.py
```

## Compatibility

Old script paths under `automation\tools` remain as wrappers that delegate to
West Kowloon project tools. This keeps existing commands alive while making
ownership clear.

## Rule

Do not put page objects, steps, project helper functions, concrete URL probes,
ZenTao delivery scripts, or evidence scripts into the platform. Start them in
the project workspace and promote only reusable abstractions.
