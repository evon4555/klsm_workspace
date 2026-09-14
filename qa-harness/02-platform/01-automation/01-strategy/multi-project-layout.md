# Multi-Project Automation Layout

Target model:

```text
D:\Workspace\
  qa-harness\
    01-system\
    02-platform\
      01-automation\
        01-strategy\
        02-src\test_automation\
        03-tools\
        04-tests\
      02-dashboard\
      03-infra\
  west-kowloon\
    01-requirements\
    02-automation\
    03-evidence\
  project-2\
    01-requirements\
    02-automation\
    03-evidence\
  project-3\
    01-requirements\
    02-automation\
    03-evidence\
```

The platform provides the runner and quality contract. A project provides the
requirements, evidence, test assets, and project adapter.

## Add A Project

1. Create `D:\Workspace\<project>\01-requirements`.
2. Create `D:\Workspace\<project>\02-automation`.
3. Create `D:\Workspace\<project>\03-evidence`.
4. Copy the project automation contract shape.
5. Add project config and environment files.
6. Point dashboard/automation smoke variables at the project fixture.
7. Run `smoke_docs.py`, `gate.py`, and the dashboard smoke.

Do not put new project features, page objects, or delivery scripts directly
under `qa-harness\02-platform\01-automation`.
