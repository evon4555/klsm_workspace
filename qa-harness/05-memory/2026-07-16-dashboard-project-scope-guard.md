# 2026-07-16 Dashboard Project Scope Guard

Scope: `D:\Workspace\qa-harness\02-platform\02-dashboard`.

Trigger: while validating the global project switcher, ZenTao Integration showed project-scoped headers but the dashboard endpoint still ignored `project` and listed global active executions.

Decision:
- Every dashboard API that accepts or implies project context must include the selected `project` in data lookup and cache keys.
- ZenTao dashboard data must use the project's mapped `zentaoExecutionId`; unmapped projects must return an explicit empty `unmapped-project` payload instead of falling back to global executions.
- Page-level ZenTao product switching should not override the global dashboard project. The product selector can display the mapped product, but should stay disabled unless a new cross-project browsing mode is explicitly designed.

Verification pattern:
- Check Standard Product returns `execution:640` and no West Kowloon execution markers.
- Check West Kowloon returns `execution:614`.
- Check Jockey Club returns `unmapped-project`.
- Browser console must have zero errors after switching projects.
