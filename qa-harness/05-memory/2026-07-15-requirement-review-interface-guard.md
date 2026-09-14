# Requirement Review Interface Guard

Date: 2026-07-15

Trigger: the user corrected multiple times that requirement consolidation must
use the decision-only working interface, but execution still picked up older
formal/internal template wording or treated a historical package as the
template source.

Decision: do not rely only on memory notes or prose rules. New user-facing
`requirement-consolidation-*.md` files must be checked by
`01-system/03-tools/check_requirement_review_interface.py`.

Applies to: dated requirement packages on or after 2026-07-15 under
`D:\Workspace`, including `standard product`, `west-kowloon`, and
`jockey club`.

Rule: the working document must use
`D:\Workspace\qa-harness\01-system\02-templates\requirement-consolidation-template.md`
as the template authority. Historical packages can be referenced only as
business prior-version evidence, not as templates. The document must use Chinese
sections for conclusion, issue classification, test scope, differences,
sources, Q/U decision tables, and next steps. It must not expose `[SECTION]`,
`Integrated Breakdown`, `Hand-Off Statement`, `Review Findings`,
`Open Review Comments`, or `Resolution / Status` to the Test Manager working
interface.

Verification: run
`python D:\Workspace\qa-harness\01-system\03-tools\check_requirement_review_interface.py`.
