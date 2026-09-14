# Path Reference Audit

Date: 2026-06-06

## Purpose

This audit records hard-coded references that remained after converting the
workspace view into physical workspace directories.

The root-level compatibility path has since been retired. Active runtime
references must use `D:\Workspace\qa-harness` or environment variables.

## Command Used

```powershell
rg -n "<old-root-path>" D:\Workspace `
  -g "!**/node_modules/**" `
  -g "!**/.venv/**" `
  -g "!**/.pytest_cache/**" `
  -g "!**/dist/**"
```

## Summary By File Type

| File type | Files with old absolute path |
|---|---:|
| `.bat` | 2 |
| `.feature` | 7 |
| `.md` | 22 |
| `.output` | 1 |
| `.ps1` | 4 |
| `.py` | 1 |

Current command result after physical workspace extraction:

```text
Count Name
----- ----
    2 .bat
    7 .feature
   22 .md
    1 .output
    4 .ps1
    1 .py
```

At the time of this audit, the `.bat` and `.ps1` references were workspace
wrappers that intentionally set or delegated through the flat compatibility
root. Most `.md` references were policy, migration notes, memory, or historical
project context. The `.feature`, `.output`, and `.py` references were project
evidence or generated/historical delivery material.

Previous baseline:

| File type | Files with old absolute path |
|---|---:|
| `.md` | 27 |
| `.py` | 17 |
| `.feature` | 7 |
| `.bat` | 4 |
| `.ps1` | 1 |
| `.yml` | 1 |
| `.yaml` | 1 |
| `.ini` | 1 |

## Highest Risk Areas

### Startup scripts

- `bootstrap.ps1`
- `start-all.bat`
- `infra/start-prometheus.bat`
- `infra/start-loki.bat`
- `infra/start-grafana.bat`

Status: addressed for core launchers.

The legacy launchers derive the repo root from script location or
`QA_HARNESS_ROOT`. Workspace wrappers should point `QA_HARNESS_ROOT` at the
workspace harness root.

### Runtime Python defaults

- `qa-system/tools/writeback_results.py`
- `qa-system/tools/regenerate_xlsx.py`
- `qa-system/tools/check_traceability.py`
- `automation/tools/update_evidence.py`
- `automation/tools/sync_md_results.py`
- `automation/tools/fixup_*.py`
- ZenTao helper scripts

Status: mostly addressed.

Common path resolution is handled by `qa-system/tools/_paths.py`, and runtime
tools now derive repo/project paths from their file location or from
`QA_HARNESS_ROOT` / `QA_WESTK_ROOT`.

The remaining `.py` reference is under project automation artifacts and is not
an active harness default.

### Grafana provisioning

Status: addressed for the supported startup path.

`infra/start-grafana.bat` sets:

```text
GF_PATHS_PROVISIONING=<qa-harness>\02-platform\03-infra\03-grafana\provisioning
QA_GRAFANA_DASHBOARDS=<qa-harness>\02-platform\03-infra\03-grafana\dashboards
```

`infra/grafana/provisioning/dashboards/dashboards.yml` uses
`$QA_GRAFANA_DASHBOARDS` instead of an absolute path.

### Project artifacts

Many West Kowloon Markdown and feature files cite old root-level paths as
evidence or source trace. These are lower runtime risk but still need either:

- historical wording kept as-is, or
- a migration note saying old evidence paths remain valid through the legacy
  junction.

The current policy is documented in `docs/historical-path-policy.md`.

## Current Approach

1. Retire the legacy root-level path after active runtime references are gone.
2. Add a workspace root convention:

   ```text
   QA_WORKSPACE_ROOT=D:\Workspace
   QA_HARNESS_ROOT=<qa-harness repo root>
   QA_WESTK_ROOT=<west-kowloon project root>
   ```

3. Keep historical project artifacts unchanged unless there is a deliberate
   evidence migration note.
4. Re-run:

   ```powershell
   .\02-platform\01-automation\.venv\Scripts\python.exe 02-platform\01-automation\03-tools\smoke_docs.py
   .\02-platform\01-automation\.venv\Scripts\python.exe 02-platform\01-automation\03-tools\smoke_dashboard.py
   .\02-platform\01-automation\.venv\Scripts\python.exe 01-system\03-tools\gate.py
   ```

5. Keep old absolute paths only in historical evidence or dated migration
   notes. Active tools should consume the numbered physical workspace layout
   directly.

The physical move gate checklist is documented in `docs/migration-gates.md`.
