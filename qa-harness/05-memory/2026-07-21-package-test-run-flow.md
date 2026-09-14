# 2026-07-21 Package Test Run Flow

Scope: QA Dashboard, Package Health, and Test Run for all D:\Workspace projects.

Trigger: Standard Product showed a latest live run (#226) with only 4 of 13 package cases, while the package had a promoted execution snapshot (#200) and a newer package-complete passed run (#217).

Decision:
- Test Run is the live execution surface and may show partial, debug, rerun, or full runs.
- Package Health is the package lifecycle and gate surface.
- A live run is not package-ready unless it matches the signed package scope and all matched cases pass.
- The execution gate must be based on a promoted fixed snapshot under `05-execution/04-execution-results`, not on the mutable latest live run.
- `07-release-feedback` is post-release loop tracking and does not block QA readiness; QA readiness is decided by stages `01` through `06`.
- In package context, Test Run must show selected run scope against the package, such as `partial / 4/13 matched`, to avoid confusing live results with package gate status.

Implementation reference:
- Backend endpoint: `GET /api/quality-system/packages/{package_id}/executions`
- Promotion endpoint: `POST /api/quality-system/packages/{package_id}/executions/{run_id}/promote`
- Frontend package gate surface: `PackageHealthPage.jsx`
- Frontend live execution surface: `TestRunPage.jsx`
