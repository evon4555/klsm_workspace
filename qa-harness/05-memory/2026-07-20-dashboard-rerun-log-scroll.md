# 2026-07-20 Dashboard Rerun Log Scroll Rule

Trigger: Rerun log modal content moved horizontally during live updates when long command/path lines were appended.

Decision: Live log components must not use `scrollIntoView()` on an inline end marker for auto-follow. That changes both vertical and horizontal scroll positions. Preserve the user's `scrollLeft` and only update `scrollTop` when new log lines arrive.

Applies: QA Dashboard live log and rerun modal UI, especially `02-platform/02-dashboard/02-frontend/src/components/LiveLog.jsx`.

Verification: In the rerun modal, a long-log case had `scrollWidth > clientWidth`. After manually setting horizontal scroll to `500`, rerun log updates and completion kept `scrollLeft=500`.
