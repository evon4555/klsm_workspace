# Cleanup Policy

Date: 2026-06-06

Scope: QA harness workspace cleanup.

Decision:

- Do not hard-delete cleanup candidates directly from the workspace.
- Move generated artifacts, debug outputs, probes, caches, and one-off run files
  to a timestamped quarantine under `D:\Backups`.
- Keep runtime dependencies such as `.venv` and `node_modules`.
- Keep compatibility junctions when old scripts, validators, or historical
  paths still need them.
- Ignore numbered junction aliases in git so the same content is not tracked
  twice through both physical and view paths.

Current cleanup quarantine:

```text
D:\Backups\qa-harness-cleanup-20260606-171426
```

Status:

- Workspace artifacts were cleared from `qa-harness\artifacts`.
- West Kowloon automation runtime artifacts were cleared from
  `west-kowloon\automation\artifacts`.
- Python/test caches outside `.venv` were cleared.
- Cleanup manifest and move results were written under the quarantine folder.

Follow-up from post-validation cleanup:

- Keep `west-kowloon\automation\artifacts\perf_latest_*.csv` when the
  dashboard is running; `/api/perf/report` reads these files for the latest
  performance report.
- `qa-harness\platform\automation\artifacts` is a compatibility junction to
  `west-kowloon\automation\artifacts`; treat the West Kowloon path as the
  physical project evidence location.
- Do not kill a non-listening backend Python parent process by itself. The
  actual listener on port `8002` can depend on that parent lifecycle.
