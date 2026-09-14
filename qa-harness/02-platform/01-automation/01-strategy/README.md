# Automation Strategy

This folder defines how the QA harness approaches automation across projects.

The platform owns the automation architecture and reusable runtime. Projects own
their concrete automated tests.

## Boundary

Platform-owned:

- BDD and pytest execution model
- Playwright/browser lifecycle convention
- traceability key convention
- dashboard recording contract
- reporting/logging primitives
- project onboarding contract
- compatibility rules during migration

Project-owned:

- page objects
- step definitions
- feature files
- project API tests
- project performance scripts
- project credentials schema and environment files
- evidence-generation and delivery scripts

## Current Runtime

The runtime remains at:

```text
D:\Workspace\qa-harness\02-platform\01-automation
```

The old flat compatibility entry has been retired; use the numbered path above.

## Read Next

- `project-contract.md`
- `multi-project-layout.md`
