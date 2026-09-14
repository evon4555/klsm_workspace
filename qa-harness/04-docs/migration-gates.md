# Migration Gates

Date: 2026-06-06

## Current State

`D:\Workspace` is now the human-facing workspace. The reusable harness, platform
areas, company context, docs, memory, artifacts, and West Kowloon project
workspace have been physically extracted into it.

The old root-level compatibility entry has been retired. Current scripts and
docs should resolve through `D:\Workspace\qa-harness`.

## Gate 1 — Runtime Path Cleanup

Status: done.

Required:

- startup scripts derive repo root from script location or `QA_HARNESS_ROOT`
- runtime Python tools derive repo/project roots
- Grafana provisioning is not tied to a fixed repo path
- `.bat`, `.ps1`, `.ini`, `.yml`, `.yaml` active runtime files have no old
  repo absolute path

## Gate 2 — Active Documentation Cleanup

Status: done.

Required:

- install, run, troubleshooting, and active developer docs use `<repo>` or
  relative commands
- docs explain `D:\Workspace` as the human-facing view
- historical evidence path policy is explicit

## Gate 3 — Static Verification

Status: done for the workspace structure phase.

Required:

```powershell
.\02-platform\01-automation\.venv\Scripts\python.exe 02-platform\01-automation\03-tools\smoke_docs.py
.\02-platform\01-automation\.venv\Scripts\python.exe -m py_compile <changed python files>
```

Also run:

```powershell
.\02-platform\01-automation\.venv\Scripts\python.exe 01-system\03-tools\gate.py
```

Run `02-platform\01-automation\03-tools\smoke_dashboard.py` only when the five dashboard services
are running; it is an end-to-end service smoke, not a static structure check.

## Gate 4 — Physical Move Decision

Status: done for the current broad structure refactor.

Gate 1-3 passed before the first project extraction. West Kowloon was moved to
`D:\Workspace\west-kowloon`; during migration the old path remained available
as a junction:

```text
<old-root>\requirements\西九 -> D:\Workspace\west-kowloon
```

The QA system was then moved to `D:\Workspace\qa-harness\01-system`; during
migration the old path remained available as a junction:

```text
<old-root>\qa-system -> D:\Workspace\qa-harness\01-system
```

The remaining harness areas were moved next:

```text
D:\Workspace\qa-harness\04-docs
D:\Workspace\qa-harness\05-memory
D:\Workspace\qa-harness\03-context\company
D:\Workspace\qa-harness\02-platform\01-automation
D:\Workspace\qa-harness\02-platform\02-dashboard
D:\Workspace\qa-harness\02-platform\03-infra
D:\Workspace\qa-harness\06-artifacts
```

West Kowloon-specific automation assets now live in:

```text
D:\Workspace\west-kowloon\02-automation
```

The old automation compatibility junctions have since been retired. Current
runtime paths use numbered physical directories.

Recommended order:

1. keep the legacy root alive during transition - done; now retired
2. move `requirements\西九` to `D:\Workspace\west-kowloon` - done
3. move `qa-system` to `D:\Workspace\qa-harness\01-system` - done
4. move remaining harness areas to `D:\Workspace\qa-harness` - done
5. split first-pass West Kowloon automation ownership - done
6. run doc smoke, gate, and dashboard smoke
7. retire compatibility junctions and keep only physical numbered directories - done
