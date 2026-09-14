# West Kowloon Evidence

This folder stores West Kowloon project evidence that should be preserved
outside the reusable QA harness.

Use it for:

- manual execution records
- automation run evidence selected for review
- screenshots, logs, reports, and exported dashboards
- performance-test CSVs, charts, and analysis selected for review
- defect triage records
- release or delivery proof

Keep transient automation output in `..\02-automation\07-artifacts` while a run is
active. Move or copy only durable evidence here when it needs to support
review, audit, delivery, or later project memory.

## Automation Evidence Promotion

Automation runtime output is not automatically trusted evidence. Promote only
selected runs into `automation\...` when the result will support review, release
readiness, delivery proof, or a Quality Gate decision.

Use:

```powershell
python D:\Workspace\west-kowloon\02-automation\04-tools\promote_automation_evidence.py `
  --run-id <dashboard-run-id> `
  --module website/login-registration `
  --env SIT `
  --build <build-or-release-id>
```

Each promoted package must include `manifest.json`. The QA dashboard reads these
manifests to determine which Quality System deliverables are backed by evidence.
Manual dashboard checkboxes may show work in progress, but final gate trust
comes from evidence manifests and their `gate.trusted` value.
