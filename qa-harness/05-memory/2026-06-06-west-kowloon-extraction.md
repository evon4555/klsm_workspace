# West Kowloon Extraction Memory

Date: 2026-06-06
Scope: West Kowloon project workspace

## Decision

West Kowloon is now a physical first-level project workspace under
`D:\Workspace`.

```text
D:\Workspace\west-kowloon
```

The legacy repo path remains as a compatibility junction:

```text
D:\qa-harness\requirements\西九 -> D:\Workspace\west-kowloon
```

## Why

This matches the intended workspace model:

```text
D:\Workspace\
  qa-harness\
  west-kowloon\
  project-2\
  project-3\
```

It also preserves old absolute paths for scripts, historical evidence, and
project documents while the migration continues.

## Backup

Created before the move:

```text
D:\Backups\qa-harness-20260606-145019
```

The backup includes the repo copy, workspace-view copy, manifest, git status,
and staged/workingtree patch files.
