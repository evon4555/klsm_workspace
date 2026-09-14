# SSO Module Index

Module purpose:

- Customer-facing single sign-on for West Kowloon websites, with AnTank acting
  as the unified C-end login entry and OAuth IdP for WestK, myWestK, M+, HKPM,
  and the AnTank ticketing website.
- Scope includes SP redirect, OAuth authorization/token exchange, silent SSO,
  old WestK Email user compatibility, registration handoff, optional login
  broadcast, optional global logout, and cross-system account/session handling.

Package convention:

- Use direct date packages under this module, for example `2026-07-13`.
- Do not create a nested change-wrapper folder for new work.
- If two independent same-day changes need separate tracking, use
  `yyyy-mm-dd-story-<id>-<short-topic>`.
- Keep `<date-package>\package.md` in every date package as the traceability
  entry point.

Timeline:

| Package | Type | Status | Source | Change summary | Next workflow step |
|---|---|---|---|---|---|
| `2026-07-13` | new-requirement | test-case review signed off; execution in progress | ZenTao story `4305` + `AnTank-consumer-unified-SSO` business/design PDFs dated 2026-06-17 | Introduces AnTank as the single C-end login entry and OAuth IdP for WestK-family SP sites, replacing the prior dual-login direction and expanding prior SSO smoke coverage into a full integration scope. | Continue execution evidence capture under `2026-07-13\05-execution` and the signed-off test case workbook. |

Maintenance rule:

- Update this timeline whenever a date package is added or its workflow status
  changes.
- Use each package's `<date-package>\package.md` for source, affected modules,
  outputs, and open questions.
- Existing login-registration SSO cases are impact references only unless the
  signed consolidation explicitly instructs a versioned update.
