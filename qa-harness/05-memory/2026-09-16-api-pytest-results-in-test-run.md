# API pytest results in Test Run (2026-09-16)

- Trigger: West Kowloon pytest API cases existed but the Test Run page only
  listed Behave scenarios, leaving API executions visible only in API Monitor.
- Decision: the API suite session-finish hook posts all collected pytest
  results to `/api/runs/import-api`; the dashboard stores them as
  `run_kind=api` with explicit, stable `case_id` values.
- Display rule: pure `api_smoke`, `api_contract`, and `api_functional` rows use
  `Automation Type = API`; `api_ui_mixed` remains `Mixed`.
- Collection rule: use pytest report hooks so fixture-level skips are retained.
  Do not use an autouse yield fixture as the result source because setup skips
  never resume that fixture.
- Verification: run #232 imported 80 rows (59 passed, 21 skipped), with zero
  missing Case IDs; the run detail endpoint loaded in about 0.14 seconds after
  bypassing Behave/XLSX enrichment for API runs.
- Run-history picker: keep it searchable. Match run ID, API/Full type, status,
  execution totals, and formatted date so mixed run histories can be narrowed
  without scrolling through every entry.
