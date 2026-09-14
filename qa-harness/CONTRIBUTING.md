# Contributing to qa-harness

This repo uses the numbered physical workspace layout under `D:\Workspace`.
Do not use retired aliases such as `automation`, `dashboard`, `infra`,
`qa-system`, `requirements`, or `D:\qa-harness`.

## Setup

```powershell
cd D:\Workspace\qa-harness
.\bootstrap.ps1
```

Project environment files live in:

```text
D:\Workspace\west-kowloon\02-automation\06-envs
```

Real credentials stay out of git. `05-config\users.yml` uses environment
variable placeholders, and `.env.<env>` files provide the local values.

## Common Workflows

### Requirement And Test Case Work

Use the West Kowloon requirement workspace:

```text
D:\Workspace\west-kowloon\01-requirements
```

For Website module changes, use:

```text
D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\<module>\<yyyy-mm-dd>
```

### Automation Work

Project-owned automation belongs in:

```text
D:\Workspace\west-kowloon\02-automation
  01-features
  02-tests
  03-src
  04-tools
  05-config
  06-envs
  07-artifacts
```

Reusable harness platform code belongs in:

```text
D:\Workspace\qa-harness\02-platform\01-automation
```

Run Behave from the project automation folder with the harness venv:

```powershell
cd D:\Workspace\west-kowloon\02-automation
$env:ENV = 'sit'
D:\Workspace\qa-harness\02-platform\01-automation\.venv\Scripts\python.exe -m behave 01-features
```

### Gate And Validation

Use explicit scope for module closeout:

```powershell
cd D:\Workspace\qa-harness
.\02-platform\01-automation\.venv\Scripts\python.exe 01-system\03-tools\gate.py `
  --xlsx "D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\01-login-registration\2026-06-16\03-test-design\test-cases-registration-login.xlsx" `
  --case-prefix SIT-TC-WEB-AUTH-
```

For doc or structure changes:

```powershell
.\smoke-docs.ps1
```

For dashboard changes, start services first with `.\start-all.bat`, then run:

```powershell
.\02-platform\01-automation\.venv\Scripts\python.exe 02-platform\01-automation\03-tools\smoke_dashboard.py
```

## Path Rules

- Active scripts, indexes, and docs use numbered physical paths.
- Historical evidence may keep old absolute paths as historical facts.
- Do not recreate junction aliases for normal work.
