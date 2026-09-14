# 2026-07-20 Dashboard Scope Selector Compact Display

Trigger: The Test Run scope selector displayed long selected feature names beside `Test Case`, which could stretch or destabilize the dashboard header controls.

Decision: Full test scope must render as the short visible label `All Test Cases`. Partial multi-selected test scopes must render as a compact `+N` counter in the Test Case selector. Keep detailed scope names in hover/context text, not in the fixed control row. The Test Case scope selector should stay compact; current width is `180px`.

Applies: QA Dashboard Test Run controls, especially `02-platform/02-dashboard/02-frontend/src/components/RunControls.jsx`.

Verification: Default scope displayed `All Test Cases` at `180px`; selecting one group displayed `+1` at `180px`. `Run: All` / `Run: Selected` stayed fixed width and no page-level horizontal overflow was introduced.
