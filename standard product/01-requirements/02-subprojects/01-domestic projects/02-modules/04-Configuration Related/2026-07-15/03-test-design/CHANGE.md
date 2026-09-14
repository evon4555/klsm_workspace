# Change Log

## 2026-07-15

- Generated initial test case design after Test Manager requirement sign-off.
- Scope follows signed decisions in
  `../02-analysis/requirement-consolidation-batch-session-configuration.md`.
- Q-5 selected option `b`, so the test design covers the complete matrix of
  three session types (`seat-selection`, `admission-ticket`, `no-seat`) across
  the three in-scope batch operations.
- Q-3 selected option `a`, so downstream customer-facing smoke regression is
  not included in this package.
- Generated `test-cases-batch-session-configuration.xlsx` by cloning
  `D:\Workspace\standard product\01-requirements\01-source-documents\02-templates\TestCase_Template.xlsx`.
- QA2 self-check reduced the case set to 15 by keeping the Q-5 main-flow
  matrix and consolidating shared preview, mandatory-field, exit, and failure
  checks into shared/data-driven cases.
- Applied the Test Manager review comment `Please translate every words to
  English`: translated the test case markdown to English and regenerated the
  xlsx workbook.
- After Test Manager sign-off, created the 05-execution automation assessment
  workbook and markdown. The signed test-case workbook remains unchanged.

## 2026-07-17

- Test Manager confirmed `SIT-TC-STD-CONFIG-015` is unnecessary for this
  package.
- Removed the save-failure prompt case from the current test case markdown and
  workbook.
- Current test case count is now 14; all current-scope cases are covered by
  the valid Behave execution result in dashboard run `194`.
- Run `176` and run `190` are superseded for execution-review purposes; run
  `194` is the current source because API write/update evidence proves state
  transition from a different precondition value to the target value.

## 2026-07-18

- Test Manager confirmed `SIT-TC-STD-CONFIG-002` should be removed from the
  current scope because the no-selection scenario depends on unstable
  list/filter data and current UI evidence is not reliable.
- Removed `SIT-TC-STD-CONFIG-002` from the current test case markdown,
  workbook, automation assessment, and live Behave execution scope.
- Current test case count is now 13. Historical run artifacts for `002` remain
  retained as superseded evidence, but must not be used as current execution
  proof.
- Mixed automation evidence for `SIT-TC-STD-CONFIG-013` now requires one API
  call summary evidence image for setup/action/readback plus a final Playwright
  UI assertion screenshot for the business check point.
