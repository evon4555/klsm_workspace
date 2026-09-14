# 06-defect-triage

Track execution defects, reruns, fix verification, and accepted risks here.

| Item | Current Status |
|---|---|
| Automation defects from latest valid run | None open from dashboard run `194`. |
| Manual-only case risk | None. `SIT-TC-STD-CONFIG-015` was removed from current scope on 2026-07-17. |
| Rerun required | Not required for automated scope after run `194`, unless code or environment changes. |

If a defect is found during manual execution or rerun, record the defect ID,
owner, fix version, verification result, and linked evidence before moving to
`06-execution-review`.
