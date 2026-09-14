# Website Module Package Migration Record

Date: 2026-06-16

Decision:

- Keep `01-source-documents` as the rolling PRD/source-input history.
- Keep `02-modules` as the generated working view by module.
- Store requirement-change outputs directly under each affected module by date:
  `02-modules\<module>\<yyyy-mm-dd>`.
- Do not recreate the old top-level Website changes entry.

Completed migration:

- Login/registration package:
  `02-modules\01-login-registration\2026-06-16`
- Project detail / ticketing package:
  `02-modules\03-ticketing\2026-05-17`

Cleanup applied:

- Removed the old top-level Website changes entry.
- Removed duplicate legacy input aliases after verifying matching files under
  numbered folders.
- Normalized `01-source-documents` so `01-mindmap`, `02-prd`, `03-Figma`, and
  `04-Others` are real visible folders, not hidden legacy folders or junctions.
- Rewrote active input indexes to point only at current numbered folders and
  date-direct module packages.
- Rechecked active README, strategy, review, and test-design documents after
  the manual folder adjustments; corrected remaining package-relative references
  to numbered folders and dated source paths.
- Included hidden iteration history in the path sweep so old package-relative
  references no longer pollute future repository searches.

Validation:

- Login/registration files were verified against the pre-migration hash
  manifest with legacy aliases mapped to numbered folders.
- Project detail / ticketing files were verified by hash against the
  pre-migration manifest.
- Markdown links and active input indexes were revalidated after folder
  normalization; no broken targets remain.
- AUTH scoped gate passed after the test-case scope cleanup.
