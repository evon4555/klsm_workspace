# Active Runbook Cleanup Memory

Date: 2026-06-06
Scope: system-wide documentation and workspace operation

## Decision

Active install, run, troubleshooting, and developer docs should not teach a
fixed repo install path as a requirement.

Use:

```text
<repo>
commands relative to repo root
QA_HARNESS_ROOT
QA_WESTK_ROOT
```

Historical project artifacts may still preserve old evidence paths per
`docs/historical-path-policy.md`.

## Applied Now

- active runbooks were changed to use `<repo>` and relative commands
- `D:\Workspace\qa-harness` now exposes `docs\` and `memory\`
- `D:\Workspace\set-workspace-env.ps1` sets workspace env vars for the current
  PowerShell session

## Verification

`automation\tools\smoke_docs.py` passed after the cleanup.
