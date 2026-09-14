---
rule_id: westk-change-package-classification
title: Same module does not automatically mean old test cases should be modified
scope: project-permanent
created: 2026-07-07
origin: "User concern during `08-discount/2026-07-07` intake: new requirement under same module must not damage existing test cases"
applies_to: [West Kowloon Website requirement packages]
candidate_for_promotion: no
promoted_to: null
promoted_at: null
---

## Rule

For West Kowloon Website requirement work, classify a new source drop by
package/story intent before editing test cases. A requirement under the same
module folder is **not** automatically a change to existing test cases.

Default behavior:

1. Create or use the dated package for the new source drop.
2. Produce `package.md` and Step 3.5 requirement consolidation first.
3. Treat previous same-module packages as impact references only.
4. Do not modify prior package test cases unless the consolidation document
   explicitly confirms replacement, deletion, or changed assertions.
5. If prior cases must change, snapshot the current version and update through
   that package's `CHANGE.md` versioning process.

Folder naming helps but is not the only signal:

- Use `yyyy-mm-dd` for one coherent delivery thread.
- Use `yyyy-mm-dd-story-<id>-<short-topic>` when same-day same-module changes are
  independent enough that shared status would hide ownership or review scope.

Classification indicators:

- **New requirement:** new story/PRD thread, additive capability, no explicit
  replacement of previous behavior.
- **Requirement change:** source says replace/remove/modify a prior rule, or the
  new behavior changes expected results of existing signed-off cases.
- **Adjacent impact:** source introduces a scenario that should be regression
  checked against older behavior but does not itself rewrite old assertions.
