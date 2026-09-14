# QA System Extraction Memory

Date: 2026-06-06
Scope: reusable QA system

## Decision

The reusable QA system is now a physical workspace directory:

```text
D:\Workspace\qa-harness\system
```

The legacy repo path remains as a compatibility junction:

```text
D:\qa-harness\qa-system -> D:\Workspace\qa-harness\system
```

## Tooling Guard

Before moving, these tools were updated to resolve paths through
`qa-system/tools/_paths.py`:

- `gate.py`
- `check_rule_drift.py`
- `maintenance_scan.py`

`_paths.repo_root()` now checks `QA_HARNESS_ROOT`, current working directory,
and script-location ancestors so old-path commands still work.

## Verification

Both gate entry points passed after the move:

```text
D:\qa-harness\qa-system\tools\gate.py
D:\Workspace\qa-harness\system\tools\gate.py
```

The workspace entry should be run after `D:\Workspace\set-workspace-env.ps1`.
