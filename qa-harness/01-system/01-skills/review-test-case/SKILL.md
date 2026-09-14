---
name: review-test-case
description: Use this skill to review QA test cases, test checklists, or AI-generated test cases for coverage, executability, traceability, clarity, expected results, evidence requirements, priority, duplicates, missing edge cases, regression impact, and alignment with business risk.
---

# Review Test Case

## Purpose

Act as an independent QA reviewer.

The goal is to find missing coverage, unclear execution steps, weak expected results, incorrect priority, missing evidence requirements, and risks that could cause escaped defects.

## Inputs

Use any available input:

- Test cases
- Requirement
- Test strategy
- Requirement risk review
- Acceptance criteria
- User flow
- Defect history
- Regression scope
- Previous approved test case version, when reviewing v2+ or a requirement-change update

If requirement context is missing, review the test cases based on stated assumptions and flag context gaps.

## Reference Documents

When available, align with:

- `../../01-quality-principles.md`
- `../../02-qa-workflow.md`
- `../../04-quality-gates.md`
- `../../05-evidence-standard.md`
- `../../templates/test-case-review-template.md`

## Workflow

1. Understand the requirement and intended test scope.
2. Check requirement-to-case traceability.
3. Review coverage by risk category.
4. Review executability of steps, preconditions, and data.
5. Review expected results for observability.
6. Review priority and evidence requirements.
7. For v2+ case sets, compare format and writing style against the previous approved version.
8. Identify duplicates, gaps, and weak cases.
9. Provide a final review decision.

## Review Areas

Check:

- Main flow coverage
- Alternative flow coverage
- Negative scenario coverage
- Boundary values
- Permission and role behavior
- Data state and data consistency
- Integration points
- Compatibility risks
- Regression impact
- Non-functional concerns
- Evidence requirements
- Version format/style continuity for v2+ changes
- West Kowloon ticket-type flow split, when applicable: `Admission ticket`
  (门票) and `seat-selection ticket` (座票) must be covered separately or have
  an explicit `NA` rationale.
- **Description wording quality** — one grammatical sentence, one scenario, one primary check. See `Description Wording Checks` below.
- **Test Steps wording quality** — one atomic action per numbered step, one persona for the whole case, one branch/data-variant. See `Test Steps Wording Checks` below.

## Output Format

Use this structure:

```markdown
# Test Case Review

---

## [SECTION] Review Summary

- Review target:
- Requirement / feature:
- Overall result: Pass / Needs Revision / Reject
- Main concern:

---

## [SECTION] Coverage Review

| Coverage Area | Status | Finding | Required Action |
|---|---|---|---|
| Main flow | Covered / Partial / Missing |  |  |
| Negative scenario | Covered / Partial / Missing |  |  |
| Boundary value | Covered / Partial / Missing |  |  |
| Permission | Covered / Partial / Missing |  |  |
| Data state | Covered / Partial / Missing |  |  |
| Integration | Covered / Partial / Missing |  |  |
| Regression | Covered / Partial / Missing |  |  |
| Ticket type flow split | Covered / Partial / Missing / NA | For West Kowloon ticketing-related scopes, check Admission ticket and seat-selection ticket coverage separately. |  |

---

## [SECTION] Findings

| Severity | Issue | Impact | Suggested Fix |
|---|---|---|---|
| Critical / High / Major / Minor |  |  |  |

---

## [SECTION] Recommended Additions

| Suggested Case | Reason | Priority |
|---|---|---|
|  |  |  |

---

## [SECTION] Final Decision

- Decision:
- Required changes:
- Reviewer notes:
```

## Review Rules

- Be direct and specific.
- Findings should explain the quality risk, not only formatting issues.
- Do not pass cases that lack observable expected results.
- Do not pass medium-risk or high-risk cases without evidence requirements.
- If requirement context is missing, mark the review as conditional.
- For v2+ reviews, unexplained format/style drift is a **High** severity
  finding. The case set cannot pass until new and modified rows match the
  previous approved version's structure, numbering, field granularity, and
  wording style.
- For West Kowloon ticketing-related scopes, missing `Admission ticket` or
  `seat-selection ticket` coverage is a coverage gap unless the case set
  documents why that ticket type is out of scope or not applicable.
- Focus on preventing escaped defects and unclear execution.

## Description Wording Checks

Scan every Test Case Description for the anti-patterns listed in
`write-test-case/SKILL.md § Description Wording Rules`. For each hit, raise a
finding using this severity map:

| Pattern found in Description | Severity | Required Fix |
|---|---|---|
| `;` connecting two subject-verb clauses (e.g., "guest ... ; logged-in ...") — two cases smashed into one | **Major** | Split into two cases (one per subject category). |
| Two subject categories with different behaviors named in one sentence (with or without `;`) | **Major** | Split into two cases. |
| ` - ` (space-hyphen-space) used as sentence connector or "namely" dash | **Minor** | Rewrite as one grammatical sentence; move enumerated items to Expected Result bullets. |
| `+` used to concatenate checkpoints inside Description | **Major** if the concatenated items are independently observable checkpoints (they belong in Expected Result); **Minor** if it is a sloppy shorthand within one checkpoint | Move each `+` item to its own Expected Result bullet, or split into separate cases if orthogonal. |
| `:` followed by a list of things to verify, or `and` chaining two independently observable predicates | **Major** | Description states the one scenario under test; each observable predicate becomes its own Expected Result bullet. |

Additional description checks:

- The Description must be **one grammatical sentence** starting with "Verify" (or the project's configured verb, e.g., `验证` in Chinese case sets — see `project-context.md`).
- The Description must read cleanly **without looking at Steps or Expected Result**. Apply the Reader Test from `write-test-case/SKILL.md § Reader test` — if it fails any of the three questions, raise a finding.
- Punctuation inside Description is limited to: sentence-final period, commas for grammatical clauses, parentheses for annotation, and hyphens inside compound words (`opt-in`, `logged-in`, `3-language`). Anything else needs justification.

## Test Steps Wording Checks

Scan every case's Steps column for the anti-patterns listed in
`write-test-case/SKILL.md § Test Steps Wording Rules`. Severity map:

| Pattern found in Steps | Severity | Required Fix |
|---|---|---|
| A step (or later step) starts with a persona/role switch — "As GUEST:", "As LOGGED-IN:", "Switch to admin:" — after an earlier step used a different persona | **Major** | Split into separate cases, one per persona. Persona is set in step 1 and never changes within a case. |
| `;` chaining two actions inside one numbered step (e.g., "1. Select Mobile; observe OTP field.") | **Minor** if the two actions are trivially close; **Major** if they are separate user actions with observable outcomes between them | Number them separately. |
| `and` chaining two distinct UI actions inside one numbered step (e.g., "Start an order and select Mobile") | **Minor** — same fix as `;` | Number them separately. `and` is only clean when the joined items name the same atomic action from two angles. |
| `wrong/correct`, `valid/invalid`, or any `X/Y` slash naming two scenario variants | **Major** | Split into two cases (positive and negative), each with a deterministic outcome. |
| An "observe" / "confirm" / "verify" / "check" step that is not a prerequisite for the next action | **Major** | Move the assertion to Expected Result; Steps hold actions only. |
| The case's Steps require the tester to perform actions in two different branches (e.g., mobile branch and email branch) | **Major** | Split into one case per branch. |

Additional steps checks:

- Every numbered step should describe **one atomic action performed by one persona**. If the tester has to do two things in step N, number them as two steps.
- Persona (guest / logged-in / admin) is established in step 1 (login state) and does not change for the remainder of the case.
- Branch / data-variant (EMAIL vs MOBILE, positive vs negative, HK vs mainland) is fixed for the whole case; a case that "runs both branches" is two cases with a shared preamble.
- Assertions live in Expected Result, not Steps. The only assertions allowed inside Steps are prerequisites for the next action (e.g., "Wait for the OTP email to arrive, then enter it.").
