# Path Root Refactor Memory

Date: 2026-06-06
Scope: system-wide path conventions

## Decision

Keep the old physical repo at `D:\qa-harness` for now, but stop new runtime
code from depending on that absolute path.

Supported overrides:

```text
QA_WORKSPACE_ROOT=D:\Workspace
QA_HARNESS_ROOT=<qa-harness repo root>
QA_WESTK_ROOT=<west-kowloon project root>
QA_GRAFANA_DASHBOARDS=<qa-harness>\infra\grafana\dashboards
```

Default behavior should derive paths from script/file location.

## Applied Now

- startup scripts derive the repo root, with `QA_HARNESS_ROOT` override
- Python tools derive repo/project roots or use `qa-system/tools/_paths.py`
- Grafana provisioning is driven by env vars from `infra/start-grafana.bat`
- old absolute path hits dropped from `.py` 17 to 3 and from `.bat` 4 to 0

## Do Not Rewrite Yet

Historical Markdown, feature files, and ZenTao delivery text still mention
`D:\qa-harness`. Treat those as evidence-path history until a migration note is
approved.

Active runbooks should not keep teaching `D:\qa-harness` as a required path.
Use `<repo>` or commands relative to the repo root.

## Related Files

- `docs/path-reference-audit.md`
- `docs/workspace-structure.md`
- `docs/historical-path-policy.md`
- `docs/migration-gates.md`
- `qa-system/tools/_paths.py`
- `infra/start-grafana.bat`
