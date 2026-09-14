# QA Workflow


---

## [SECTION] Purpose

This workflow defines how QA work should move from requirement review to release and continuous improvement.

The goal is to make testing predictable, traceable, and repeatable across projects.

---

## [SECTION] Workflow Overview

1. Requirement intake
2. Requirement risk review
3. Test strategy
3.5. Requirement consolidation and scope sign-off (Test Manager gate)
4. Test case design
5. Test case review
6. Test execution
7. Defect management
8. Regression testing
9. Test report
10. Execution review / release readiness
11. Release feedback monitoring
12. Retrospective and improvement

---

## [SECTION] 1. Requirement Intake

QA should collect the available requirement context before test design starts.

Required inputs:

- Requirement description
- Business goal
- User flow or acceptance criteria
- Design or UI reference, if applicable
- API or integration documentation, if applicable
- Mindmap or structured outline, if the project uses one
- Data rules
- Permission rules
- Delivery timeline
- Known dependencies
- **Source authority order** for this project (from `project-context.md`): which source is authoritative, which are reference, how to handle items present in only one source. See `07-source-authority.md`.

Output:

- Requirement input package
- Source authority confirmed (or surfaced as a question if not declared)
- Open questions list

---

## [SECTION] 2. Requirement Risk Review

**Status in West Kowloon / Antank pipeline: conditional.**

This step produces a standalone risk review artifact. By default the
work it covers — ambiguity surfacing, risk categorization, initial test
scope suggestion — is absorbed into Step 3.5's consolidation document
for routine requirement packages. Invoke this step as a separate
artifact only when one of these triggers fires:

- The requirement's risk level is **High** in its consolidation doc, and
  the team needs a dedicated risk writeup for stakeholders beyond QA.
- New project kickoff in an unfamiliar domain (regulated industry,
  novel integration, new payment rail) — risk landscape is wider than
  one requirement package can capture.
- Production-bug retrospective requires a backwards-looking risk review
  feeding `analyze-production-bug`.

For all other packages, do **not** produce a separate risk review file
— let the consolidation doc carry the risk content. This avoids
parallel artifacts that drift.

QA should identify ambiguity and risk before writing detailed test cases.

Review areas:

- Business risk
- User flow risk
- Data risk
- Permission risk
- Integration risk
- Compatibility risk
- Performance risk
- Security risk
- Regression risk
- Operational risk

Output:

- Requirement risk review notes
- Questions for product, design, development, or operations
- Initial test scope suggestions

**Use:** [skills/review-requirement-risk/SKILL.md](./01-skills/review-requirement-risk/SKILL.md). No dedicated template — output is free-form risk notes.

---

## [SECTION] 3. Test Strategy

**Status in West Kowloon / Antank pipeline: conditional (project / subproject scope).**

This step produces a project-level or subproject-level test strategy
artifact. By default it is **not** invoked per requirement package —
per-package scope, types, environment, automation opportunity, and exit
criteria are all captured in the Step 3.5 consolidation doc. Invoke
this step as a separate artifact only when:

- **Project kickoff** for a new project under the harness.
- **New subproject** lands (e.g., Website added to a project that
  previously only had Box Office).
- A cross-package release plan needs an explicit strategy artifact for
  stakeholders.

The non-functional adjunct skills (`create-automation-plan`,
`create-performance-test-plan`, `create-security-checklist`) follow the
same conditional rule: invoke per project or per release scope, not per
requirement package, unless the consolidation doc explicitly flags a
non-functional concern that warrants a dedicated workbook.

QA should define how the feature or project will be tested.

The strategy should include:

- Test scope
- Out-of-scope items
- Test types required
- Role assignment
- Environment plan
- Test data plan
- Regression scope
- Automation opportunity
- Non-functional test needs
- Major risks and mitigations
- Entry and exit criteria

Output:

- Test strategy document

**Use:** [skills/create-test-strategy/SKILL.md](./01-skills/create-test-strategy/SKILL.md) → fills [templates/test-strategy-template.md](./02-templates/test-strategy-template.md).

**Adjuncts (run as part of the same strategy phase when scope warrants):**

- Automation scope: [skills/create-automation-plan/SKILL.md](./01-skills/create-automation-plan/SKILL.md) → [templates/automation-strategy-template.md](./02-templates/automation-strategy-template.md).
- Performance scope: [skills/create-performance-test-plan/SKILL.md](./01-skills/create-performance-test-plan/SKILL.md) → [templates/performance-test-plan-template.md](./02-templates/performance-test-plan-template.md).
- Security scope: [skills/create-security-checklist/SKILL.md](./01-skills/create-security-checklist/SKILL.md) → [templates/security-test-checklist.md](./02-templates/security-test-checklist.md).

---

## [SECTION] 3.5. Requirement Consolidation And Scope Sign-Off

**Gate step.** Before any test case is written, QA produces one consolidated
requirement document that synthesizes everything read so far, then waits
for the Test Manager to sign off on scope. Test case design is blocked
until sign-off lands.

The document collects:

- Conclusion first: `有没有问题？`
- Issue classification
- Test scope / capability list — capabilities re-organized by business
  function, not by source-doc structure
- **Differences (差异项)** — three labelled diffs: vs previous version,
  vs standard product (for SaaS contexts where a project is overriding
  standard product behavior), vs adjacent module
- Source inventory
- **Decision table** — `Q-1..Q-n` items with two-or-three-option
  proposals and an empty `答复` column
- **Assumption table** — `U-1..U-n` source gaps with an empty
  `确认 / 修正` column
- **Next step / sign-off gate** — what the Test Manager fills and when
  `03-test-design` can start

Output:

- `02-analysis/requirement-consolidation-<scope>.md` per package
- `02-analysis/requirement-consolidation-<scope>.docx` generated for the
  Test Manager handoff
- Sign-off recorded by the Test Manager editing the pre-filled human
  reviewer row in place (the AI must not self-sign-off)

The Test Manager working interface is the fixed decision-only Chinese
template in `02-templates/requirement-consolidation-template.md`. It must not
show internal `[SECTION]` markers, `Integrated Breakdown`,
`Hand-Off Statement`, `Review Findings`, `Open Review Comments`, or other
QA-owned maintenance fields. Formal review/sign-off layouts may be generated
for external packages only when explicitly requested, and must not replace the
decision-only Q/U working document.

**Use:** [skills/consolidate-requirement/SKILL.md](./01-skills/consolidate-requirement/SKILL.md) → fills [templates/requirement-consolidation-template.md](./02-templates/requirement-consolidation-template.md).

**Template governance:** canonical templates live in
`01-system/02-templates/`. A historical package can be used as business
evidence or as an extraction source for improving a template, but it must not
be used as the runtime template. Run
`python 01-system/03-tools/check_template_governance.py` after changing
templates, skills, or workflow docs.

**Guard:** run `python 01-system/03-tools/check_requirement_review_interface.py`
after producing or changing a requirement consolidation. This is also wired
into `gate.py`.

**Gate rule:** `03-test-design/` MUST NOT contain new test cases for this
package until the consolidation doc reaches **Signed Off** status. When
the Test Manager updates the doc with answers, treat the updated
document — not the raw sources — as the authoritative scope statement
for test design.

---

## [SECTION] 4. Test Case Design

QA writes or generates test cases based on the agreed scope and risks.

Coverage should include:

- Main business flow
- Alternative flow
- Negative scenario
- Boundary values
- Data state changes
- Permission behavior
- Error handling
- Compatibility
- Regression impact
- Project-specific split dimensions, such as West Kowloon `Admission ticket`
  versus `seat-selection ticket` for ticketing-related flows

Output:

- Test case list
- Requirement-to-case traceability

If an already-reviewed test-case set is changed later, the change must be
visible in the artifacts reviewers open. For every added, modified, removed, or
post-sign-off scope-adjusted case:

- Update the current `03-test-design/test-cases-<scope>.md/.xlsx` first.
- Record the reason in `03-test-design/CHANGE.md`.
- Add or update the workbook `Audit Trail` sheet with date, actor, change
  type, reason, affected case IDs, current scope impact, and evidence links.
- If a previous workbook is available, highlight added/modified case cells in
  yellow and add comments explaining why the change was needed.
- If `05-execution/02-automation-assessment/automation-assessment-<scope>.xlsx`
  already exists, update its `Audit Trail` as well.

Use `01-system/03-tools/record_testcase_change.py` for the workbook/review
trail writeback and `01-system/03-tools/check_testcase_audit_trail.py` to
validate that the xlsx and docx surfaces still match.

**Use:** [skills/write-test-case/SKILL.md](./01-skills/write-test-case/SKILL.md) → fills [templates/test-case-template.md](./02-templates/test-case-template.md) (or the xlsx test case template under `<project>/01-requirements/01-source-documents/02-templates/` when a project provides one).

---

## [SECTION] 5. Test Case Review

Test cases should be reviewed before execution for important or risky work.

Review criteria:

- Requirement coverage
- Risk coverage
- Clear preconditions
- Executable steps
- Observable expected results
- Correct priority
- Duplicates and gaps
- Regression relevance
- Version format/style continuity for v2+ test case changes (**High**)
- Project-specific split dimensions are covered or explicitly marked `NA`,
  including West Kowloon `Admission ticket` versus `seat-selection ticket`
  when ticketing/cart/checkout/payment/discount/refund/wallet/order behavior is
  in scope

Output:

- Test case review result
- Required changes
- Final approved test case list

**Use:** [skills/review-test-case/SKILL.md](./01-skills/review-test-case/SKILL.md) → fills [templates/test-case-review-template.md](./02-templates/test-case-review-template.md).

AI review artifacts belong under `03-test-design/.iterations/`.
`04-test-case-review/` is reserved for the final human/Test Manager sign-off
form and its paired `.docx`.

If the project provides a human-facing test case review template under
`<project>/01-requirements/01-source-documents/02-templates/`, use that
template for the `04-test-case-review/` `.docx` sign-off form. Do not use
the QA2 AI review checklist as the human sign-off form.

For human review comments, update the affected test-case artifacts before
closing the comment: revise `03-test-design/test-cases-<scope>.md`, regenerate
the `.xlsx`, update `03-test-design/CHANGE.md`, and add a closure row to
`Review Trail and Version Record`. The `Open Review Comments` field in the
final conditions/next-step section is the sign-off gate signal: `None` means
the reviewer has no open comments; actionable comments block sign-off and
require re-review after AI changes.

For post-review or post-sign-off case changes, the `Review Trail and Version
Record` row is not sufficient by itself. The matching workbook must also carry
an `Audit Trail` row, and the human-facing review DOCX must be regenerated
from the updated markdown. This applies to add, modify, remove, and scope
adjustment decisions. MD-only audit notes are not acceptable because the
reviewer primarily works from `.xlsx` and `.docx`.

For v2+ reviews, compare against the previous approved case file. Do not pass a
new version that changes row format, wording style, numbering, enum labels, or
field granularity just because a different AI/model wrote it.

**Adjunct:** if the project already has automation, also run [skills/review-automation-coverage/SKILL.md](./01-skills/review-automation-coverage/SKILL.md) to confirm important flows are covered.

**Iterate to Pass (closed AI loop, no human between rounds):** for cases that need
several review→revise cycles, use [skills/iterate-test-case-quality/SKILL.md](./01-skills/iterate-test-case-quality/SKILL.md)
as the orchestrator — it chains `write-test-case` → `review-test-case` →
[skills/revise-test-case/SKILL.md](./01-skills/revise-test-case/SKILL.md) → re-review,
stopping at Pass or a 3-round hard cap. Use this when the user asks for
"iterative" / "auto-improve" test case generation; otherwise stick with the
single-shot review above.

**On requirement-change handoff:** when a new dated xlsx lands per `10-change-management.md`,
use [skills/maintain-requirement-change/SKILL.md](./01-skills/maintain-requirement-change/SKILL.md)
to chain `diff_xlsx_versions.py` → `maintenance_scan.py` → cleanup of features/.
That skill is the implementation runbook for the change-management policy.

---

## [SECTION] 6. Test Execution

QA executes test cases and records evidence.

Execution records should include:

- Tester
- Date
- Environment
- Build or version
- Test case result
- Screenshot, log, API response, or other evidence
- Defect link if failed
- Risk note if partially tested or blocked

Output:

- Test execution record
- Defect list
- Evidence package

**Use:** [templates/test-execution-record-template.md](./02-templates/test-execution-record-template.md) for the record; [templates/test-evidence-checklist.md](./02-templates/test-evidence-checklist.md) to confirm evidence completeness. Evidence-completeness is also verified by `01-system/03-tools/validate_evidence.py` against the xlsx execution columns.

---

## [SECTION] 7. Defect Management

Defects should be tracked with enough information for reproduction and impact judgment.

Defect records should include:

- Summary
- Environment
- Preconditions
- Steps to reproduce
- Actual result
- Expected result
- Evidence
- Severity
- Priority
- Impact scope
- Owner
- Fix version
- Verification result

Output:

- Defect list
- Fix verification records

**Use:** [templates/bug-report-template.md](./02-templates/bug-report-template.md). The dashboard's "Open Bug" button auto-fills a ZenTao bug from a failed scenario using this template's structure.

---

## [SECTION] 8. Regression Testing

Regression testing verifies that existing important behavior still works after changes.

Regression scope should be based on:

- Changed modules
- Dependent modules
- Historical defect areas
- Critical business flows
- Integration points
- Automation coverage
- Release risk

Output:

- Regression plan
- Regression execution evidence

**Use:** [skills/create-regression-plan/SKILL.md](./01-skills/create-regression-plan/SKILL.md) → fills [templates/regression-plan-template.md](./02-templates/regression-plan-template.md).

---

## [SECTION] 9. Test Report

QA summarizes execution status, quality conclusion, known risks, and QA
readiness recommendation.

The report should include:

- Scope tested
- Scope not tested
- Execution summary
- Defect summary
- Remaining risks
- Evidence links
- QA readiness recommendation

Output:

- Test report

**Use:** [skills/generate-test-report/SKILL.md](./01-skills/generate-test-report/SKILL.md) → fills [templates/test-report-template.md](./02-templates/test-report-template.md). Pulls execution data straight from `dashboard/backend/dashboard.db` when available.

---

## [SECTION] 10. Execution Review / Release Readiness

After execution, QA reviews whether the tested scope is ready for release
consideration. QA records readiness and risk, but does not own the final
business release decision.

Review items:

- Test strategy completed
- Required cases executed
- Critical defects resolved or accepted
- Regression completed
- Evidence available
- Risks documented
- Automated and manual results reconciled
- QA readiness outcome recorded

Output:

- Execution review / QA readiness sign-off

**Use:** [templates/execution-review-checklist.md](./02-templates/execution-review-checklist.md). Historical links to [templates/release-quality-checklist.md](./02-templates/release-quality-checklist.md) are compatibility aliases only; new packages use `execution-review-checklist.md`. The outcome is recorded as `Ready for Release`, `Ready for Release with Accepted Risk`, `Not Ready - Fix Required`, `Blocked`, or `Scope Change Required`, backed by `01-system/03-tools/gate.py` and dashboard execution data for the latest harness state.

---

## [SECTION] 11. Release Feedback Monitoring

After release or deployment feedback is available, QA and the project team
record feedback and feed escaped issues or improvements into later requirement
packages.

Monitor:

- Production defects
- User complaints
- Error logs
- Monitoring alerts
- Performance changes
- Data issues

Output:

- Post-release quality notes
- Production issue list

**Use:** for any production issue that escaped testing, [skills/analyze-production-bug/SKILL.md](./01-skills/analyze-production-bug/SKILL.md) → fills [templates/production-bug-analysis-template.md](./02-templates/production-bug-analysis-template.md). The improvement actions feed into step 12 below.

---

## [SECTION] 12. Retrospective And Improvement

Important issues should improve the QA system.

Review:

- What escaped testing
- Why it escaped
- Which process failed
- Which source was missed or under-consulted
- Which template or skill should change
- Whether training is needed
- Whether automation or monitoring should be added

Output:

- Retrospective notes
- Improvement actions
- Training plan if needed
- Updates to `project-context.md`, `07-source-authority.md`, or skill/template files when the retrospective reveals a methodology gap (not just a feature gap)

**Use:** [skills/qa-retrospective-coach/SKILL.md](./01-skills/qa-retrospective-coach/SKILL.md) → fills [templates/qa-retrospective-template.md](./02-templates/qa-retrospective-template.md). When the retrospective surfaces a worker-skill gap, also run [skills/worker-training-plan/SKILL.md](./01-skills/worker-training-plan/SKILL.md) → fills [templates/worker-training-plan-template.md](./02-templates/worker-training-plan-template.md).

---

## [SECTION] Skill ↔ Workflow Step Coverage Matrix

Quick reference — confirms every skill and template has a home in the
12-step workflow above, and every step has at least one supporting
artifact. If you add a new skill or template, add it here too.

| Step | Skill(s) | Template(s) |
|---|---|---|
| 1. Requirement intake | — (collection only) | — |
| 2. Risk review *(conditional — see § 2)* | `review-requirement-risk` | — |
| 3. Test strategy *(conditional — see § 3, project / subproject scope)* | `create-test-strategy` + `create-automation-plan` + `create-performance-test-plan` + `create-security-checklist` | `test-strategy-template` + `automation-strategy-template` + `performance-test-plan-template` + `security-test-checklist` |
| 3.5. Requirement consolidation (Test Manager gate, **default per-package entry point**) | `consolidate-requirement` | `requirement-consolidation-template` |
| 4. Test case design | `write-test-case` | `test-case-template` (or project xlsx template) |
| 5. Test case review | `review-test-case` + `review-automation-coverage` + `iterate-test-case-quality` + `revise-test-case` + `manage-review-signoff` + `maintain-requirement-change` | `test-case-review-template` |
| 6. Test execution | — | `test-execution-record-template` + `test-evidence-checklist` |
| 7. Defect management | — | `bug-report-template` |
| 8. Regression | `create-regression-plan` | `regression-plan-template` |
| 9. Test report | `generate-test-report` | `test-report-template` |
| 10. Execution review | — | `execution-review-checklist` + `release-quality-checklist` (compatibility alias) |
| 11. Release feedback monitor | `analyze-production-bug` | `release-feedback-template` + `production-bug-analysis-template` |
| 12. Retrospective | `qa-retrospective-coach` + `worker-training-plan` | `qa-retrospective-template` + `worker-training-plan-template` |
| Cross-cutting: Translation review *(mandatory after any translation, see § Cross-cutting)* | `review-translation-quality` | (no template — output shape in skill) |

**Total**: 19 skills used, 16 templates used. Zero orphans. Verified by `01-system/03-tools/check_workflow_coverage.py` (run as part of `gate.py`).

---

## [SECTION] Cross-cutting: Translation Review

Translation is not a workflow step — it can happen at any handoff
(consolidation docx for an English-speaking reviewer; test cases for
international partners; test reports for stakeholders). Whenever a
translation IS produced, the [`review-translation-quality`](./01-skills/review-translation-quality/SKILL.md)
skill is **mandatory** before the translation is delivered.

The rule lives here, not in any one step, because it cuts across:

- Step 3.5 (consolidation docx EN version for international stakeholders)
- Step 4 (test cases EN version for offshore execution / review)
- Step 9 (test report EN version)
- Step 11 (escape-analysis EN version when sharing with global teams)

What this means in practice:

- After producing a translated artifact, the AI must run
  `review-translation-quality` against source + target BEFORE
  reporting "done"
- The output is a structured defect report (Critical / High / Medium /
  Minor) saved next to the translation as a review note
- Medium+ findings → produce v2 fixing them; only ship after v2
- See `12-md-docx-handoff.md` for the docx-side mechanics (translations
  often ride on top of docx export)
