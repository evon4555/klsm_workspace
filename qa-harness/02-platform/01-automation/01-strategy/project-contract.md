# Project Automation Contract

Every project that uses the QA harness should expose this shape:

```text
<project>\
  01-requirements\
  02-automation\
    01-features\
    02-tests\
      api\
      performance\
    03-src\test_automation\
      web\
    04-tools\
    05-config\
    06-envs\
    07-artifacts\
  03-evidence\
```

Do not create project-root compatibility aliases for normal work. Use the
numbered physical folders directly.

## Required Contracts

- Scenario names start with the canonical case ID, for example
  `SIT-TC-WEB-AUTH-009 ...`.
- Project page objects stay under the project `02-automation\03-src`.
- Project step definitions stay under the project
  `02-automation\01-features\steps`.
- Project delivery scripts stay under the project `02-automation\04-tools`.
- Project-generated files stay under the project `02-automation\07-artifacts`
  or `03-evidence`.
- Platform code must not hard-code a project URL, product ID, account, or
  requirement path unless it is a documented default fixture.

## Platform And Project Boundary

The platform and project trees are separate physical folders:

```text
D:\Workspace\qa-harness\02-platform\01-automation
D:\Workspace\west-kowloon\02-automation
```

Future projects should get their own project workspace and project profile
rather than adding their files into the platform runtime.
