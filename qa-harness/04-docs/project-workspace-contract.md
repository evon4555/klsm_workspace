# Project Workspace Contract

Date: 2026-06-06

Every concrete project under `D:\Workspace` should use this visible top-level
contract:

```text
project-x\
  01-requirements\
  02-automation\
  03-evidence\
```

Compatibility aliases named `requirements`, `automation`, and `evidence` should
not be created for new project work. The current workspace uses physical
numbered folders only.

Git is optional for a solo project workspace. If a project is not in git, use
dated source folders, versioned filenames, and index notes to identify the
current artifact. Add git when collaboration, formal review, rollback history,
or commit-level audit becomes necessary.

## 01-requirements

Owns project facts:

- source documents
- stable project overview
- subprojects or workstreams
- module-specific requirement changes
- test design, reviews, and requirement traceability

Recommended internal shape:

```text
01-requirements\
  00-project-overview\
  01-source-documents\
  02-subprojects\
    01-<subproject>\
      01-source-documents\
      02-modules\
        01-<module>\
          <yyyy-mm-dd>\
```

Put change packages directly under the owning module by source/change date:
`02-modules\<module>\<yyyy-mm-dd>`. Do not create a subproject-level
change-package folder outside modules for new work; if a change appears
cross-module, create affected module date packages and cross-reference them from
the package indexes.

## 02-automation

Owns project-specific automation assets:

- feature files and step definitions
- page objects and project adapters
- API and performance tests tied to the project
- project config, users, endpoints, and environment files
- project delivery scripts
- transient run artifacts

Recommended shape:

```text
02-automation\
  01-features\
  02-tests\
  03-src\
  04-tools\
  05-config\
  06-envs\
  07-artifacts\
```

Reusable runners, framework primitives, strategy, and platform tooling belong
under `D:\Workspace\qa-harness\02-platform\01-automation`.

## 03-evidence

Owns durable project evidence:

- selected automation reports
- manual execution evidence
- screenshots, logs, and exported dashboards
- defect triage exports
- release and delivery proof

Do not put durable project evidence under the shared harness. Promote only
project-neutral lessons back to `D:\Workspace\qa-harness\01-system` or
`D:\Workspace\qa-harness\05-memory`.

## Compatibility Rule

Use physical numbered directories by default. A compatibility junction is only
allowed as a short-lived migration exception with a dated note, an owner, and a
retirement condition. Active indexes and runbooks must point to the physical
numbered paths.

## LLM-Neutral Memory Rule

Project memory must not depend on one assistant's private state. For every
project under `D:\Workspace`, durable workflow rules, project skills, template
decisions, and review/sign-off decisions should be recorded in visible workspace
files.

Recommended entry files:

```text
project-x\
  AGENTS.md
  CODEX.md
  CLAUDE.md
```

User-local agent folders, such as Codex or Claude private memory locations, are
allowed as launchers or convenience copies only. If they conflict with visible
workspace files, the visible workspace files win.
