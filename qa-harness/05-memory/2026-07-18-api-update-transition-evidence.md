# 2026-07-18 API Update Transition Evidence

Scope: QA harness automation and execution evidence for API write/update cases
under `D:\Workspace`.

Trigger: User found that `SIT-TC-STD-CONFIG-005` evidence showed before and
after as the same saleable group, so the screenshot did not prove the API
actually changed the business value.

Decision: API update automation must follow the signed test case description
and prove the core business point. For value-change cases, a pass requires a
different precondition value, the real write request, and readback evidence that
changed from the precondition to the target. Final-state-only evidence is
insufficient and must be superseded by a new run.
