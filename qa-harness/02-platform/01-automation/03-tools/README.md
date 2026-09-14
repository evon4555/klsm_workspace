# 02-automation/04-tools/

Platform-level tools for the reusable automation runtime.

## Platform Tools

| Script | Purpose |
|---|---|
| `smoke_dashboard.py` | End-to-end smoke for dashboard, observability, Behave recording, and performance chain. Defaults to the West Kowloon fixture but can be pointed at another project through env vars. |
| `smoke_docs.py` | Static documentation and link-integrity smoke for the harness docs. |
| `_project_tool.py` | Compatibility launcher for project-owned tools that used to live here. |

## Project Tool Compatibility

Concrete project scripts now live under the project workspace:

```text
D:\Workspace\west-kowloon\02-automation\04-tools
```

This platform folder keeps thin wrappers for some old platform entry-point
names. For example:

```powershell
.\02-platform\01-automation\.venv\Scripts\python.exe D:\Workspace\west-kowloon\02-automation\04-tools\update_evidence.py
```

delegates to:

```text
D:\Workspace\west-kowloon\02-automation\04-tools\update_evidence.py
```

New project-specific scripts should be created in the project workspace, not in
this platform folder.

## Dashboard Smoke Project Overrides

Use these variables to make `smoke_dashboard.py` exercise another project:

```text
QA_SMOKE_FEATURE
QA_SMOKE_SCENARIO_NAME
QA_PERF_HOST
QA_PERF_LOCUSTFILE
```

The default values keep the current West Kowloon smoke fixture working.
