# 05-execution

Workflow steps 6–7 (test execution + defect management). Owner: **QA1**.

Expected outputs: test execution records, evidence under `evidence/` (screenshots, logs, API responses), defect list.

## Records

- [test-execution-record-registration-login.md](./test-execution-record-registration-login.md)
  — SIT-TC-WEB-AUTH-001..035 dry run, 2026-05-22. 34 cases: 25 Pass, 1 Fail, 8 NA.
  Automated with Behave + Playwright (pure-UI) in `D:\Workspace\west-kowloon\02-automation`.
  1 confirmed defect: DEF-1 (duplicate-email registration allowed — TC004).

## Evidence

`evidence/` holds the step-screenshot strips (`registration-TC00X-<status>-<date>.png`).
The same strips are embedded into column S of `..\03-test-design\test-cases-registration-login.xlsx`.

Re-generate results + evidence any time:

```
cd D:\Workspace\west-kowloon\02-automation
$env:ENV = "sit"
D:\Workspace\qa-harness\02-platform\01-automation\.venv\Scripts\python.exe 04-tools\update_evidence.py          # all 34 cases -> .xlsx
D:\Workspace\qa-harness\02-platform\01-automation\.venv\Scripts\python.exe 04-tools\update_evidence.py 010 029  # subset re-run
D:\Workspace\qa-harness\02-platform\01-automation\.venv\Scripts\python.exe 04-tools\sync_md_results.py                # mirror .xlsx -> .md
```

Or, on the QA dashboard's Test Run page, use the scope-aware **Sync → xlsx**
button — it runs `update_evidence.py` for the selected modules from the UI.

Note: embedded images live only in the `.xlsx`. If the workbook is regenerated
from the `.md`, re-run `update_evidence.py` to restore the screenshots.
