# Platform And Project Automation Split

Date: 2026-06-06

## Intent

`qa-harness` is the reusable QA system and execution platform. West Kowloon is a
concrete project that consumes the harness and contributes reusable lessons back
only after they are proven project-neutral.

The automation tree previously mixed both concerns. This split gives the project
its own automation home without breaking old Behave, pytest, and dashboard
commands.

## Current Ownership

West Kowloon owns:

```text
D:\Workspace\west-kowloon\02-automation\01-features
D:\Workspace\west-kowloon\02-automation\02-tests\api
D:\Workspace\west-kowloon\02-automation\03-src\test_automation\web
D:\Workspace\west-kowloon\02-automation\05-config
D:\Workspace\west-kowloon\02-automation\06-envs
D:\Workspace\west-kowloon\02-automation\07-artifacts
```

The harness platform owns:

```text
D:\Workspace\qa-harness\02-platform\01-automation\02-src\test_automation\config
D:\Workspace\qa-harness\02-platform\01-automation\02-src\test_automation\reporting
D:\Workspace\qa-harness\02-platform\01-automation\02-src\test_automation\cli.py
D:\Workspace\qa-harness\02-platform\01-automation\02-src\test_automation\logging.py
D:\Workspace\qa-harness\02-platform\01-automation\02-src\test_automation\pytest_plugin.py
D:\Workspace\qa-harness\02-platform\01-automation\04-tests\app
D:\Workspace\qa-harness\02-platform\01-automation\04-tests\web
D:\Workspace\qa-harness\02-platform\01-automation\03-tools\smoke_dashboard.py
D:\Workspace\qa-harness\02-platform\01-automation\03-tools\smoke_docs.py
D:\Workspace\qa-harness\02-platform\01-automation\01-strategy
```

## Current Physical Paths

Compatibility junctions have been retired. Project-owned scripts live in:

```text
D:\Workspace\west-kowloon\02-automation\04-tools
```

The old root-level repo path has been retired. Use the workspace platform path
above for current commands.

## Deferred Cleanup

Some platform code still carries West Kowloon defaults as smoke fixtures. Treat
those as configurable defaults, not ownership. Do not add new project scripts to
the platform runtime.

## Verification Notes

After the split, path-sensitive smoke code must not infer the harness root from
`Path(__file__).resolve().parents[2]`. Junction resolution now points tools at
their physical workspace locations, not necessarily the command entry path.

Current rule:

- harness-level tools should prefer `QA_HARNESS_ROOT`
- project-level tools should prefer `QA_WORKSPACE_ROOT` / `QA_WESTK_ROOT`
- dashboard sync from Behave must resolve `dashboard.db` through
  `D:\Workspace\qa-harness\02-platform\02-dashboard\01-backend`

## Memory Rule

Durable lessons should be written to `05-memory\YYYY-MM-DD-topic.md`, then promoted
to `01-system` only when they are reusable beyond West Kowloon. This follows the
memory principle of carrying useful context forward, obeying current constraints,
and keeping stale context reviewable.
