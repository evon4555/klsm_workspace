# Website Map / Accessibility Map

Scope:

- website sitemap / accessibility-map quick-entry page
- business entry shortcuts shown in the map
- parameterized links from the map to project, activity, membership-card, user,
  order, and venue-filter pages
- footer content listed from the current footer sections

New module-specific changes should go directly under dated folders in this
module, for example `2026-06-29`.

Source rule:

- Treat `..\..\01-source-documents` as the broader PRD/source-input history
  when a source file is promoted there.
- Treat this folder as the generated accessibility-map working view.
- For each dated update that affects the accessibility map, create a separate
  dated package directly under this module instead of adding a nested
  change-wrapper folder.
- Each dated package should include `package.md` and the standard numbered
  output folders: `01-input`, `02-analysis`, `03-test-design`,
  `04-test-case-review`, `05-execution`, `06-execution-review`, and
  `07-release-feedback`.
- Keep raw user-provided source files in `01-input`; put derived analysis,
  case design, review, execution evidence, and release notes in the later
  numbered folders.
