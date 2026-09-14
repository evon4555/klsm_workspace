# QA Dashboard Test-Version Architecture Decision

Date: 2026-08-06

Trigger: Architecture review found growing backend coupling, duplicated project
metadata, stale in-memory run state, and weak database/runtime governance.

Decision:

- Keep the dashboard as a React/Vite + FastAPI modular monolith.
- Centralize project mappings in the dashboard-owned visible project profile.
- Recover interrupted runs at backend startup and strengthen SQLite with WAL,
  foreign keys, schema versioning, and indexes.
- Support a built Vite bundle served by FastAPI while retaining Vite HMR for development.
- Add focused backend/frontend validation around project profiles, recovery,
  database runtime, and static hosting.
- Because this is still a test version, do not yet add mutation-endpoint
  authentication, Locust path allowlisting, or load-target allowlisting.

Applies to: `D:\Workspace\qa-harness\02-platform\02-dashboard`.

Review trigger: Revisit the deferred security controls before binding the
backend beyond loopback, sharing it with other users, or treating it as a
production service.
