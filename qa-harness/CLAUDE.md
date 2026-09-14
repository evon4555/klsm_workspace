# Claude Notes - qa-harness

This file is auto-loaded at the qa-harness root. Keep active guidance pointed
at the numbered physical workspace layout.

For LLM-neutral workspace rules, also read `AGENTS.md`. Claude-local memory is
not the canonical source for harness rules.

## Workspace Model

```text
D:\Workspace\
  qa-harness\       reusable QA system, platform, docs, memory
  west-kowloon\     current West Kowloon project workspace
```

The retired `D:\qa-harness` root and workspace-internal junction aliases should
not be used for active work. Use environment roots when scripts need stable
absolute paths:

```text
QA_WORKSPACE_ROOT=D:\Workspace
QA_HARNESS_ROOT=D:\Workspace\qa-harness
QA_WESTK_ROOT=D:\Workspace\west-kowloon
```

## QA Designer Entry

1. Read [01-system/README.md](./01-system/README.md).
2. Follow [01-system/02-qa-workflow.md](./01-system/02-qa-workflow.md).
3. Use [01-system/01-skills/](./01-system/01-skills/README.md) for risk review, test case, and report drafting.
4. Keep West Kowloon deliverables under `D:\Workspace\west-kowloon\01-requirements`.
5. Before saying "tested", run [01-system/03-tools/gate.py](./01-system/03-tools/README.md) with an explicit xlsx scope.

## Automation Entry

1. Harness platform: [02-platform/01-automation/](./02-platform/01-automation/).
2. Project features: `D:\Workspace\west-kowloon\02-automation\01-features`.
3. Project page objects: `D:\Workspace\west-kowloon\02-automation\03-src\test_automation\web`.
4. Project tools and evidence writeback: `D:\Workspace\west-kowloon\02-automation\04-tools`.
5. Dashboard DB: `D:\Workspace\qa-harness\02-platform\02-dashboard\01-backend\dashboard.db`.

## DevOps Entry

1. Install: [INSTALL.md](./INSTALL.md).
2. Start/stop: `.\start-all.bat` / `.\stop-all.bat`.
3. Infra: [02-platform/03-infra/README.md](./02-platform/03-infra/README.md).
4. Dashboard backend: [02-platform/02-dashboard/01-backend/README.md](./02-platform/02-dashboard/01-backend/README.md).

## Required Smokes

```powershell
.\02-platform\01-automation\.venv\Scripts\python.exe 02-platform\01-automation\03-tools\smoke_docs.py
.\02-platform\01-automation\.venv\Scripts\python.exe 02-platform\01-automation\03-tools\smoke_dashboard.py
.\02-platform\01-automation\.venv\Scripts\python.exe 01-system\03-tools\gate.py --help
```

Run `D:\Workspace\qa-harness\02-platform\01-automation\03-tools\smoke_dashboard.py`
only when the dashboard services are up. For static structure/doc changes,
`D:\Workspace\qa-harness\02-platform\01-automation\03-tools\smoke_docs.py` and
targeted `py_compile` are enough.
