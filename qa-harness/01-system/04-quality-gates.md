# Quality Gates


---

## [SECTION] Purpose

Quality gates define the minimum conditions required before work can move to the next stage.

They make release quality less dependent on informal judgment and personal habits.

---

## [SECTION] Gate 1: Requirement Ready

Before test strategy and detailed test case design, the requirement should meet these conditions:

- Business goal is clear.
- Scope is defined.
- Acceptance criteria are available or agreed.
- User flow is understandable.
- Major data rules are known.
- Permission rules are known.
- Dependencies are identified.
- Open questions are recorded.
- Requirement risk review is completed for medium-risk or high-risk work.

If this gate is not passed:

- Do not finalize test cases.
- Record unclear points.
- Ask product, design, development, or operations for clarification.

---

## [SECTION] Gate 2: Test Design Ready

Before test execution, the test design should meet these conditions:

- Test strategy is completed for non-trivial work.
- Test scope and out-of-scope items are clear.
- Required test types are identified.
- Test cases cover core business flows.
- Negative, boundary, permission, data, and regression scenarios are considered.
- Test data and environment are available or planned.
- Test cases are reviewed for important or risky work.

If this gate is not passed:

- Do not start full execution.
- Fix coverage, environment, data, or review gaps first.

---

## [SECTION] Gate 3: Test Execution Complete

Before a feature is marked as tested, these conditions should be met:

- Required test cases are executed.
- Execution result is recorded.
- Evidence is attached or linked.
- Failed cases have defect records.
- Blocked or skipped cases have reasons.
- Fix verification is completed for resolved defects.
- Remaining risks are documented.

If this gate is not passed:

- Do not mark testing as complete.
- Continue execution or document explicit risk acceptance.

---

## [SECTION] Gate 4: Regression Complete

Before release, regression conditions should be reviewed:

- Regression scope is defined.
- Critical business flows are covered.
- Impacted modules are covered.
- Historical defect areas are considered.
- Automated regression results are reviewed if available.
- Manual regression evidence is collected where needed.
- Regression risks are documented.

If this gate is not passed:

- Do not recommend release without explicit risk acceptance.

---

## [SECTION] Gate 5: Execution Review Complete

Before QA marks a package ready for release consideration, these conditions
should be met:

- Test report is available.
- Test scope and not-tested scope are clear.
- Automated and manual execution results are reconciled.
- Critical and high severity defects are resolved or accepted.
- Regression is complete or risk-accepted.
- Performance and security risks are reviewed when relevant.
- Known risks are documented.
- QA readiness outcome is stated.
- Execution review sign-off is recorded.

If this gate is not passed:

- Do not mark the package ready for release consideration. Continue execution,
  reduce scope, fix defects, block the package, or record formal risk
  acceptance.

---

## [SECTION] Gate 6: Release Feedback Closed

After release, closure requires:

- Production monitoring is checked.
- Production defects are recorded.
- Escaped defects are analyzed.
- Accepted risks are reviewed for follow-up.
- Improvement actions are created for important issues.
- Templates, skills, automation, or training plans are updated when needed.

If this gate is not passed:

- Do not consider the quality cycle complete.

---

## [SECTION] Risk Acceptance

Risk acceptance must be explicit.

Risk acceptance should include:

- Risk description
- Business impact
- Reason for acceptance
- Owner
- Expiration or follow-up date
- Mitigation plan

---

## [SECTION] Gate Severity Guidance

- Low-risk changes may use lightweight evidence and simplified review.
- Medium-risk changes should complete strategy, case review, execution evidence, regression, and report.
- High-risk changes should include explicit quality owner review, stronger regression, and relevant non-functional checks.
