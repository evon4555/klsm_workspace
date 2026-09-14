# Service Smoke Path Fixes

Date: 2026-06-06
Scope: workspace migration, automation smoke, dashboard sync

## Observation

After moving automation under `D:\Workspace\qa-harness\platform\automation` and
project assets under `D:\Workspace\west-kowloon\automation`, tools that used
`Path(__file__).resolve().parents[2]` started resolving the wrong root.

Two concrete failures appeared:

- `smoke_docs.py` treated `D:\Workspace\qa-harness\platform` as the repo root.
- Behave `features/environment.py` looked for `west-kowloon\dashboard` and
  skipped dashboard DB recording.

## Decision

Path-sensitive tools must prefer explicit roots:

```text
QA_HARNESS_ROOT=D:\qa-harness
QA_WORKSPACE_ROOT=D:\Workspace
QA_WESTK_ROOT=D:\Workspace\west-kowloon
```

`QA_HARNESS_ROOT` intentionally points to the flat compatibility root until all
validators can consume the nested workspace layout directly.

## Verification

After the fixes:

```text
smoke_docs.py: PASS 15/15
gate.py: OVERALL PASS
smoke_dashboard.py: PASS 28/28
```

The dashboard smoke inserted Behave run rows correctly after the DB path fix.
