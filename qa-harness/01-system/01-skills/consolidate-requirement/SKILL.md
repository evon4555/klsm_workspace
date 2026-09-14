---
name: consolidate-requirement
description: Use this skill AFTER requirement intake / risk review / test strategy and BEFORE writing any test case. It produces a single consolidated requirement document using the canonical decision-only Q/U template: conclusion, issue classification, test scope, differences, sources, decision questions, and assumption confirmations. Test case design is gated on the user's confirmation of this document.
---

# Consolidate Requirement

## Purpose

Produce one human-readable checkpoint document that synthesizes everything
QA has read so far about the requirement, **before** test cases are written.
The document is the explicit hand-off between AI-driven analysis and Test
Manager scope sign-off.

This step exists because:

- Bypassing it sends test cases to review with unconfirmed scope and
  unanswered questions baked in — those churn into revise loops.
- The Test Manager needs one place to (a) see what the AI understood,
  (b) confirm scope, (c) answer open questions in one pass.
- Skipping it has caused scope drift in past packages — see
  `08-our-pipeline.md` § 1.5.

## Inputs

- All material already gathered under the package's `01-input/`.
- The package's risk review (if step 2 produced one).
- The package's test strategy (if step 3 produced one).
- Any prior-version test case file (for `差异项`-vs-previous-version).
- The standard-product reference, if this requirement is a project-specific
  override of a standard product feature (for `差异项`-vs-standard-product).
- Project source-authority order from `07-source-authority.md` and
  `project-context.md`.

If a source-authority conflict surfaces between inputs, surface it as an
Open Question — do not pick a winner.

## Reference Documents

- `../../02-qa-workflow.md` § Step 3.5
- `../../07-source-authority.md`
- `../../08-our-pipeline.md` § 1.5
- `../../10-change-management.md` — for `差异项` semantics
- `../../11-rule-promotion.md`

## Output

A pair of files at `<package>/02-analysis/`:

- `requirement-consolidation-<scope>.md` — canonical, AI-readable source.
- `requirement-consolidation-<scope>.docx` — human review derivative,
  generated immediately after the `.md`.

**User-facing template rule:** the working consolidation document shown to
the Test Manager MUST follow the fixed decision-only Chinese structure from
`02-templates/requirement-consolidation-template.md`. Historical packages may
be used as business references when they are the previous version of the same
scope, but they are not template sources.

- conclusion first: `有没有问题？`
- issue classification
- test scope
- differences
- sources
- `Q-1..Q-n` decision table with an empty `答复` column
- `U-1..U-n` assumption table with an empty `确认 / 修正` column
- next step / sign-off gate

Do not expose internal section markers or formal-review maintenance fields in
the Test Manager working interface. In particular:

- no `[SECTION]` markers
- no `Integrated Breakdown` or `Hand-Off Statement` headings
- no request for the user to fill `Review Findings`, `Open Review Comments`,
  `Resolution / Status`, workflow status, or other QA-owned fields

Formal review/sign-off renderers may still be used for an external formal
package if explicitly requested, but they must not replace the decision-only
working document.

`<scope>` should be a short slug describing the requirement, e.g.
`bank-card-priority-purchase`. If a package has multiple sub-scopes that
need separate sign-off, produce one consolidation pair per sub-scope and
list them under the package's `02-analysis/README.md` (or in package.md).

The hand-off rule (see [`../../12-md-docx-handoff.md`](../../12-md-docx-handoff.md)):

- Test Manager edits the **`.docx`**, not the `.md`.
- When the Test Manager is done, the AI reads the edited `.docx` tables
  and comments, updates the canonical `.md`, and re-renders the formal
  `.docx` with the project-approved renderer.
- The signed-off `.md` is then the authoritative scope statement for
  `03-test-design/`.

## Workflow

1. **Source inventory.** List every source under `01-input/` and any
   relevant Website-level / project-level sources. Note which is
   authoritative for this package (mindmap > PRD > Figma for West Kowloon,
   unless `project-context.md` says otherwise).
2. **Test scope / capability list.** Re-organize the requirement by business
   function (not by source-doc structure), but present it under `测试范围`
   instead of an internal `Integrated Breakdown` heading. Each entry should
   be one testable capability.
3. **Differences (`差异项`).** Identify three kinds of diff and label each
   entry with which kind it is:
   - **vs previous version of this package**, if any.
   - **vs standard product**, if this requirement is a project-specific
     add-on or override of a SaaS standard product feature. Quote the
     standard-product reference; flag whether the change is intended to
     sync back to standard or stays project-only.
   - **vs adjacent module behavior**, if this requirement changes
     behavior in a way that affects another module (e.g., introduces a
     new payment method that the order-confirmation module must surface).
4. **Test scope this round.** State explicitly:
   - **In scope** — capabilities that will produce test cases in this
     package's `03-test-design/`.
   - **Out of scope (deferred)** — capabilities present in source but
     deferred to a later package, with the reason.
   - **Out of scope (handled elsewhere)** — capabilities owned by another
     team / module / standard-product test suite, with a pointer.
   - The scope statement must be **assertable**: a reader should be able
     to point at any capability and say "yes / no / which bucket".
5. **Unclear items.** Things the source documents do not unambiguously
   answer. For each item, note the source location and the specific
   ambiguity (do not say "the PRD is unclear" — say "PRD §3.2 does not
   specify behavior when X and Y are both true").
6. **Items requiring user confirmation.** Distinct from Unclear: these
   are decisions that need a human (Test Manager or PM) to make a call.
   For each item, propose two or three options with trade-offs.
7. **Next step / sign-off gate.** End the document with `下一步`, telling the
   Test Manager to fill only the decision columns and confirming that
   `03-test-design` remains blocked until sign-off.

## Signoff Convention

The consolidation document is a working review interface, not a formal
review-admin form. Use this order:

1. Metadata table.
2. `修订历史`.
3. `有没有问题？`.
4. `问题分类`.
5. `测试范围`.
6. `差异项`.
7. `来源`.
8. `问题清单` with Q and U tables at the bottom.
9. `下一步`.

The Test Manager only fills the final decision columns in the Q/U tables.
AI owns status synchronization, package indexes, review-trail bookkeeping,
and any external formal rendering requested later.

## Gate Rule

`03-test-design/` MUST NOT contain new test cases for this package until
the consolidation doc reaches the **Signed Off** status in its Revision
History (filled by the Test Manager, not by the AI).

If the Test Manager updates the doc with answers, treat the updated
version as the authoritative scope statement and start `03-test-design`
from it — do not re-read raw sources and re-derive scope from scratch.

If sources change after sign-off (e.g., PRD revision lands), produce a
new revision of the consolidation doc with a delta-only section, and
re-request sign-off before the corresponding test cases are updated.

## Quality Rules

- Test cases for admin / back-office configuration are usually owned by
  the standard-product test suite, not the project package. When the
  source mixes admin pages and customer-facing flows, scope this
  document on the **customer-facing business behavior**, and list the
  admin pages under "Out of scope (handled elsewhere)" pointing at the
  standard-product owner. Confirm placement with the Test Manager in
  the open-questions section.
- Do NOT bake test data prep into scope items unless the data prep is
  itself a customer-facing behavior. Data setup is a test execution
  concern, not a scope decision.
- The `测试范围` capability list is not a copy-paste of the PRD outline. It
  must re-organize the requirement by business function and be readable on
  its own.
- The "differences" section must cite both the new behavior and the
  prior behavior with source references. Vague phrases like "scope
  expanded" are not acceptable.
- Every open question must have an owner (Test Manager / PM / Dev /
  Design) — questions without owners stall.
- Sign-off is recorded in the Revision History table, not as free text.
