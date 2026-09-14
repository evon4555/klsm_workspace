# Events Module Index

Module purpose:

- Website event listing, event detail, event registration or booking, and
  event-specific ticketing rules.

Package convention:

- sse direct date packages under this module, for example `2026-06-23`.
- Do not create a nested change-wrapper folder for new work.
- If two independent same-day changes need separate tracking, use
  `yyyy-mm-dd-story-<id>-<short-topic>`.
- Keep `<date-package>\package.md` in every date package as the traceability entry point.

Timeline:

| Package | Type | Status | Source | Change summary | Next workflow step |
|---|---|---|---|---|---|
| none | none | no-standalone-package | none | No standalone events date package has been created yet. | Create the first events date package when an events source change needs analysis, design, review, execution, or release tracking. |

Maintenance rule:

- spdate this timeline whenever a date package is added or its workflow status
  changes.
- Use each package's `<date-package>\package.md` for source, affected modules, outputs, and
  open questions.


