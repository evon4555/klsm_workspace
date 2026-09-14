# 2026-07-17 Behave Tag And Dashboard Display Rule

Trigger: QA Dashboard exposed confusing raw Behave tags and one automation assessment used `Smoke` as an implementation layer.

Decision:
- Test Case ID stays at the start of the Behave Scenario name and must not be duplicated as a tag.
- Business feature files use one scope tag plus exactly one layer tag: `@api`, `@ui`, or `@mixed`.
- Do not add technical guard tags such as `@real_api`, `@real_ui`, or `@mutation`; runtime protection is inferred from scope/layer tags in `environment.py`.
- Smoke is an execution scope or priority, not an implementation layer. Store the implementation layer as `API`, `UI`, or `Mixed`.
- QA Dashboard should show signed workbook descriptions and clean automation types; raw tags are internal execution metadata only.

Applies to: all `D:\Workspace` projects using QA harness Behave automation and QA Dashboard.
