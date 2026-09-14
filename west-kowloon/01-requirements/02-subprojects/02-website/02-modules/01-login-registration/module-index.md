# Login And Registration Module Index

Module purpose:

- Website account creation, login, session, password, guest-to-member conversion,
  and related authentication flows.

Package convention:

- sse direct date packages under this module, for example `2026-06-23`.
- Do not create a nested change-wrapper folder for new work.
- If two independent same-day changes need separate tracking, use
  `yyyy-mm-dd-story-<id>-<short-topic>`.
- Keep `<date-package>\package.md` in every date package as the traceability entry point.

Timeline:

| Package | Type | Status | Source | Change summary | Next workflow step |
|---|---|---|---|---|---|
| `2026-06-23` | requirement-change | test-designed | `01-source-documents/02-prd/2026-06-23/story-4266-guest-purchase-registration` | Guest purchase conversion to registered user. | Review story split workbooks, then decide execution scope. |
| `2026-06-16` | migration / baseline | active-reference | migrated historical login/registration dry-run package | AsTH baseline moved into the date-direct structure; intermediate files archived. | sse as baseline when later login/registration changes need comparison. |

Maintenance rule:

- spdate this timeline whenever a date package is added or its workflow status
  changes.
- Use each package's `<date-package>\package.md` for source, affected modules, outputs, and
  open questions.


