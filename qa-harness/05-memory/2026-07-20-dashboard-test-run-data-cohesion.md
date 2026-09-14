# 2026-07-20 Dashboard And Test Run Data Cohesion

Trigger: The Dashboard Recent Runs table showed the same Standard Product run with a different time than the Test Run page because it parsed backend UTC timestamps directly with `new Date()`.

Decision: Test Run and Dashboard must share the same run identity and time semantics. Full-run summaries use `run_kind == "full"`; reruns stay out of Dashboard trend/latest summaries. Display time should use `finished_at || started_at` through `formatDashboardTime()`, not direct `new Date()` parsing of backend ISO strings.

Applies: `02-platform/02-dashboard/01-backend/main.py`, `02-platform/02-dashboard/02-frontend/src/pages/DashboardPage.jsx`, `RunControls.jsx`, and `ResultsTable.jsx`.

Verification: For Standard Product, `/api/runs` latest full run and `/api/stats/trends` latest run both returned `#226`, `4/4 executed`, `finished_at=2026-07-20T06:25:38.248546`, `run_kind=full`, `is_rerun=false`. Dashboard Recent Runs and Test Run selector both displayed `Jul 20, 2026, 2:25 PM`.
