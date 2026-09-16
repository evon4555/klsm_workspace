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
- Visible filtering rule: provide a separate `Run Type` selector with
  `All Runs`, `API`, and `Full`. Search inside the history picker alone is not
  visually discoverable and must not be treated as the type filter.
- Sync rule: completed API imports must appear in both Test Run and the main
  Dashboard. Both pages poll for external pytest imports; Test Run follows a
  new latest run only while the user is not intentionally viewing history.
- Historical-run rule: selecting a run must show that run's stored results,
  plus only reruns belonging to the same full-run lineage. Never overwrite a
  historical run with a later independent run's status, and do not block the
  result view on bulk Excel metadata enrichment.
