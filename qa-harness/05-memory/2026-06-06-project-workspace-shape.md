# Project Workspace Shape

Date: 2026-06-06

Decision: every concrete project under `D:\Workspace` should expose the same
numbered primary folders:

```text
project-x\
  01-requirements\
  02-automation\
  03-evidence\
```

Rationale:

- `01-requirements` keeps project facts, source documents, subprojects,
  modules, requirement changes, and test design together.
- `02-automation` keeps project-specific features, steps, page objects, API
  tests, config, environment files, functions, and scripts together.
- `03-evidence` keeps durable execution proof out of the reusable QA harness.

West Kowloon was adjusted to follow this visible contract:

```text
D:\Workspace\west-kowloon\
  01-requirements\
  02-automation\
  03-evidence\
```

Historical root entries such as `requirements`, `automation`, `evidence`,
`Website`, `BoxOffice`, `00-project-overview`, and `01-source-documents` are
hidden compatibility entries. They may remain while old commands and
historical paths still need to resolve, but new work should use the numbered
folders.
