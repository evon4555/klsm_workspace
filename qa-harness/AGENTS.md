# QA Harness Agent Instructions

This folder is the shared QA system for projects under `D:\Workspace`.
Use visible harness files as the source of truth for standards, templates,
skills, validators, platform runbooks, and durable memory.

## Start Here

1. Read `README.md`.
2. Read `01-system\README.md`.
3. Follow `01-system\02-qa-workflow.md`.
4. Use `01-system\01-skills\README.md` to select the required harness skill.
5. Check `05-memory` only for durable dated lessons, not as a replacement for
   current system rules.

## LLM-Neutral Rule

Codex, Claude Code, and other agents should recover the same harness rules from
this folder. Assistant-local memory may remind the agent what to read, but it
must not be the only source of a QA rule.

## Workspace Roots

```text
QA_WORKSPACE_ROOT=D:\Workspace
QA_HARNESS_ROOT=D:\Workspace\qa-harness
QA_WESTK_ROOT=D:\Workspace\west-kowloon
```

## Validation

Run targeted validators after changing harness rules, skills, templates, or
project workflow mappings:

```powershell
python D:\Workspace\qa-harness\01-system\03-tools\check_workflow_coverage.py
python D:\Workspace\qa-harness\01-system\03-tools\check_rule_drift.py --requirements-dir D:\Workspace
```
