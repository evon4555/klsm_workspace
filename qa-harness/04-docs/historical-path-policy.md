# Historical Path Policy

Date: 2026-06-06

## Purpose

The workspace refactor separates the reusable QA harness from concrete project
work. Old root-level absolute paths may still appear in historical evidence
and delivery text.

This document defines what may be rewritten and what should stay untouched.

## Policy

### Rewrite Active Operational References

Rewrite paths in files that teach the current system how to run:

- startup scripts
- bootstrap/install docs
- runbooks and troubleshooting docs
- runtime Python defaults
- Grafana/Prometheus/Loki config used by launchers

Preferred forms:

```text
<repo>
<repo>\02-platform\01-automation
<repo>\02-platform\02-dashboard\02-frontend
QA_HARNESS_ROOT
QA_WESTK_ROOT
```

### Preserve Historical Evidence References

Do not bulk-rewrite paths inside historical evidence, project deliverables, or
ZenTao delivery summaries.

Examples:

- executed test-case rows that cite the automation location used at execution
  time
- execution reports already shared to the project
- feature-file source headers that document the original source path
- ZenTao task description/comment scripts that reproduce an already-submitted
  delivery summary

If these are confusing after physical migration, add a migration note near the
artifact instead of silently changing the historical text.

### Add Migration Notes Instead Of Rewriting Facts

Use this wording when an old evidence path needs clarification:

```text
Migration note: this artifact was produced before the workspace refactor.
The legacy root-level path was available during migration and has since been
retired. New work should use D:\Workspace and the QA_HARNESS_ROOT /
QA_WESTK_ROOT conventions.
```

## Rationale

Operational docs should describe how the system works now. Historical artifacts
should preserve what was true when the evidence was produced.
