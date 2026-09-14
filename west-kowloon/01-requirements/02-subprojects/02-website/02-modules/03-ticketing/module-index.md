# Ticketing Module Index

Module purpose:

- Website project detail ticket purchase, order creation/cancellation,
  ticketing options, and related user-visible ticketing flows.

Package convention:

- sse direct date packages under this module, for example `2026-06-23`.
- Do not create a nested change-wrapper folder for new work.
- If two independent same-day changes need separate tracking, use
  `yyyy-mm-dd-story-<id>-<short-topic>`.
- Keep `<date-package>\package.md` in every date package as the traceability entry point.

Timeline:

| Package | Type | Status | Source | Change summary | Next workflow step |
|---|---|---|---|---|---|
| `2026-05-17` | migration / baseline | active-reference | migrated project-detail ticketing package | Project detail, ticket purchase, and seat-selection design outputs moved into the date-direct structure. | sse as baseline when later ticketing changes need comparison. |

Maintenance rule:

- spdate this timeline whenever a date package is added or its workflow status
  changes.
- Use each package's `<date-package>\package.md` for source, affected modules, outputs, and
  open questions.


