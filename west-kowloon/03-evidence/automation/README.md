# Automation Evidence

This folder stores automation runs that have been selected for review, audit,
release support, or delivery proof.

Automation runtime output remains in:

```text
..\..\02-automation\07-artifacts
```

Only promote a run here when it should become durable project evidence.

## Package Layout

```text
automation\
  <subproject>\
    <module>\
      run-<dashboard-run-id>-<yyyymmdd-hhmmss>\
        manifest.json
        gate-result.json
        evidence-report.md
        raw\
          run_<id>.json
        screenshots\
        logs\
```

## Promotion

Use the project tool:

```powershell
python D:\Workspace\west-kowloon\02-automation\04-tools\promote_automation_evidence.py `
  --run-id 160 `
  --module website/login-registration `
  --env SIT `
  --build <build-or-release-id>
```

The tool copies the selected run artifacts and writes:

- `manifest.json`: machine-readable evidence metadata for the dashboard
- `gate-result.json`: trusted/not-trusted quality gate result
- `evidence-report.md`: human-readable evidence package summary

## Quality Gate Rule

An automation evidence package is trusted only when:

- it has an environment
- it has a build/version/deployment identifier
- it has scenario-level execution records
- it has the raw run JSON
- it has at least one human-reviewable artifact such as a screenshot, log, API
  evidence, or report
- it maps to Quality System deliverables
- failed or errored runs include defect links or known risks

Manual checkbox progress in the dashboard can track work in progress, but final
Quality Gate decisions should use trusted evidence packages.
