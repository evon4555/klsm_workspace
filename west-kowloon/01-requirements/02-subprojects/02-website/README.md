# Website Subproject

This folder owns Website requirements and QA outputs for West Kowloon.

Use the numbered structure:

```text
02-website\
  01-source-documents\
  02-modules\
    01-login-registration\
    02-homepage\
    03-ticketing\
    04-seat-selection\
    05-membership-card\
    06-events\
    07-merchandise\
```

Canonical model:

- `01-source-documents` stores the rolling PRD/source inputs only. New PRD
  drops and revised full-website documents belong here, grouped by date.
  Use these source subfolders:
  `01-mindmap`, `02-prd`, `03-Figma`, and `04-Others`.
- `02-modules` is the derived working view. Module folders are generated or
  refreshed from `01-source-documents`, then used for analysis, test design,
  review, and execution outputs.
- Requirement-change outputs live directly under the affected module, grouped by
  source/change date:

```text
02-modules\<module>\<yyyy-mm-dd>
```

- Each date package should keep the standard numbered folders:
  `01-input`, `02-analysis`, `03-test-design`, `04-test-case-review`,
  `05-execution`, `06-execution-review`, and `07-release-feedback`.
- Add `package.md` in each date package to trace the source PRD/story, affected
  modules, RAG retrieval result, and final decision: reuse, update, or create.
- The old top-level change area and old nested change wrapper are no longer part
  of the active Website working structure. Do not recreate them for new work.
