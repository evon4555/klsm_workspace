# Workspace Review Fixes

Date: 2026-06-06

Scope: `D:\Workspace`, `D:\qa-harness`, `D:\Workspace\west-kowloon`

Context:

The workspace was reviewed after the folder-structure refactor. The goal was
to catch bugs introduced by junctions, old ports, platform/project split, and
dashboard startup assumptions.

Fixes made:

- Vite production build from Windows junction paths now uses
  `resolve.preserveSymlinks = true`; official Vite docs define this as keeping
  file identity on the original path instead of resolving symlinks.
- Dashboard backend defaults now use port `8002`; frontend CORS and proxy docs
  are aligned with `5174/8002`.
- Project automation scripts now default to `QA_WESTK_ROOT` or the West Kowloon
  project root for project assets. `QA_HARNESS_ROOT` is reserved for harness
  and dashboard platform assets.
- ZenTao helper scripts no longer write stale `D:/qa-harness/requirements/西九`
  paths into task comments, and token-required scripts fail fast when
  `ZENTAO_API_V2_TOKEN` is missing.
- Platform `pytest` default collection now only runs platform self-tests
  (`tests/app`, `tests/web`). West Kowloon live API tests still collect and run
  from `D:\Workspace\west-kowloon\automation`.
- West Kowloon API smoke suppresses expected internal-cert warnings correctly.
- `smoke_docs.py` and `smoke_dashboard.py` use ASCII separators in console
  output to avoid Windows console mojibake.
- Dashboard frontend has a declared SVG favicon so browser smoke does not emit
  `/favicon.ico` 404.
- `start-all.bat` and infra start scripts now guard ports before launch, so
  repeated starts skip existing services instead of creating bind conflicts.
- Grafana startup now creates required provisioning and plugin directories, and
  disables update/plugin checks for this local harness use case. Grafana docs
  confirm `check_for_updates`, `check_for_plugin_updates`, and
  `reporting_enabled` are supported `[analytics]` settings.

Validation:

- `py_compile`: 113 unique Python files, 0 errors.
- Platform pytest: 2 skipped placeholders, 0 failures.
- West Kowloon L0 API smoke: 40 passed, 0 warnings after fix.
- `gate.ps1`: PASS for schema, traceability, evidence, coverage.
- `smoke-docs.ps1`: PASS 15/15.
- `smoke_dashboard.py`: PASS 28/28.
- Frontend build: PASS; Vite only reports expected large chunk warning.
- Playwright browser check: dashboard rendered with KPI cards, charts, recent
  runs, and no console errors after favicon fix.
- Screenshot evidence: `D:\Workspace\qa-harness\artifacts\playwright\dashboard-home-20260606-1812.png`.

Rules reinforced:

- Use physical paths or `rg -L` when scanning this workspace; junctions can hide
  or duplicate files.
- Do not treat Windows console mojibake as file corruption. Verify with
  UTF-8 reads before editing Chinese text.
- Keep historical `8001/5173` references only when explicitly marked as legacy;
  active dashboard runtime is `8002/5174`.
- Do not run destructive cleanup through shell-composed paths. Resolve absolute
  targets first and keep cleanup inside `D:\Workspace` or a named backup folder.

Follow-up review: 18:30-18:50

Additional fixes:

- Replaced remaining Ant Design deprecated props in dashboard frontend:
  `Card headStyle` -> `styles.header`, `Select dropdownRender` -> `popupRender`,
  and `Modal destroyOnClose` -> `destroyOnHidden`.
- Confirmed the active compatibility CORS entries for `5173` are intentional;
  the running dashboard remains `5174/8002`.
- Historical evidence still contains old `D:\qa-harness\automation` references.
  These were not bulk-edited because they describe the path used when the
  evidence was produced and are part of traceability.
- Removed plaintext credentials from the tracked platform
  `automation/config/users.yml`; the file now contains only environment
  variable placeholders. Real local values remain in ignored `envs/.env.<env>`
  files or an external secrets manager.
- Added user fixture variables to `automation/envs/.env.example` so `user1`,
  `user2`, `user3`, and `website_user` can all be configured without committing
  secrets.
- Removed two dead internal `/run/:id` links from `ResultsTable.jsx`. The
  dashboard is state-driven and has no React Router route for `/run/:id`, so
  those links could navigate users to a non-existent page.

Additional validation:

- Playwright browser checks covered Dashboard, Performance Test, API Monitor,
  ZenTao Integration, Quality System, Test Run, Email Notification, and
  Settings.
- New-tab browser checks after the Ant Design fixes showed Test Run and ZenTao
  console output with 0 errors and 0 warnings.
- `smoke_dashboard.py`: PASS 28/28 after service guard fixes; inserted run #92.
- `start-all.bat` repeat run skipped Prometheus, Loki, Grafana, backend, and
  frontend because all ports were already listening.
- Frontend production build: PASS after the Ant Design fixes; only the existing
  large chunk warning remains.
- `gate.ps1`: PASS for schema, traceability, evidence, coverage.
- `smoke-docs.ps1`: PASS 15/15.
- West Kowloon API smoke: 40 passed.
- Safe dashboard GET probe: 14 endpoints returned HTTP 200. ZenTao
  `dashboard?refresh=true` completed in 11.14s, which is slower than local
  cached reads because it refreshes from the external ZenTao source.
- Python compile check: 832 traversed `.py` files, 0 errors. Count includes
  compatibility junction duplication.
- Platform automation pytest: 2 skipped placeholders, 0 failures.
- Credential config check: platform `website_user` loaded from existing local
  env values, platform pytest still passed with 2 expected skips, and ignored
  `.env.local/.env.sit/.env.uat` files are covered by `.gitignore`.
- Frontend dead-link check: no remaining `/run/` hrefs in dashboard source;
  frontend build still passes after the change.

Git-root migration: 19:00-19:32

What changed:

- Moved the repository `.git` directory from `D:\qa-harness` to
  `D:\Workspace\qa-harness`.
- Promoted `D:\Workspace\qa-harness` to the canonical git root.
- Renamed the old physical root to
  `D:\qa-harness.backup-20260606-192521`.
- Re-created `D:\qa-harness` as a junction to
  `D:\Workspace\qa-harness`, so existing commands and historical paths still
  resolve.
- Added hidden flat compatibility entries in the workspace root:
  `automation`, `dashboard`, `infra`, `qa-system`, `requirements`, and
  `company`.
- Replaced the thin workspace `start-all.bat`, `stop-all.bat`, and
  `bootstrap.ps1` wrappers with real root scripts that resolve the repository
  from their script location.
- Updated `gate.ps1` and `smoke-docs.ps1` to default
  `QA_HARNESS_ROOT` to `D:\Workspace\qa-harness`.
- Updated `smoke_docs.py` so workspace physical/numbered duplicate views do not
  create false broken-link findings.
- Added `context/README.md`, which became required once the workspace root was
  the doc smoke root.

Validation after migration:

- `git -C D:\Workspace\qa-harness rev-parse --show-toplevel` returns
  `D:/Workspace/qa-harness`.
- `git -C D:\qa-harness rev-parse --show-toplevel` also returns
  `D:/Workspace/qa-harness` through the compatibility junction.
- The backup directory does not contain `.git`; the only active repository root
  is the workspace root.
- Git status after moving root has 0 delete lines.
- With `QA_HARNESS_ROOT=D:\Workspace\qa-harness`:
  `gate.ps1` PASS, `smoke-docs.ps1` PASS 16/16, platform pytest 2 expected
  skips, frontend build PASS, West Kowloon API smoke 40 passed, dashboard smoke
  PASS 28/28.
- With `QA_HARNESS_ROOT=D:\qa-harness` through the junction:
  `gate.ps1` PASS, `smoke-docs.ps1` PASS 16/16, dashboard smoke PASS 28/28.
