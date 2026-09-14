# Evidence Standard


---

## [SECTION] Purpose

This document defines what evidence is required before QA work can be considered complete.

The purpose is to make testing traceable, reviewable, and improvable.

---

## [SECTION] Definition Of Tested

A feature or change can be marked as tested only when:

- Test scope is clear.
- Test cases or test checklist are available.
- Execution result is recorded.
- Evidence is attached or linked.
- Defects are tracked.
- Blocked, skipped, or untested areas are documented.
- Final quality conclusion is stated.

---

## [SECTION] Required Evidence Types

#### [POINT] Requirement Evidence

Use when reviewing or testing a requirement.

Required items:

- Requirement link or identifier
- Business goal
- Acceptance criteria
- Open questions
- Requirement risk notes

#### [POINT] Test Design Evidence

Use before execution.

Required items:

- Test strategy or testing notes
- Test cases or checklist
- Requirement-to-case mapping for important features
- Review result for medium-risk or high-risk features

#### [POINT] Test Execution Evidence

Use during and after execution.

Required items:

- Tester
- Execution date
- Environment
- Build, version, branch, or deployment identifier
- Test case result
- Screenshot, log, API response, database check, video, or other proof
- Defect link for failed cases
- Reason for skipped or blocked cases

#### [POINT] Defect Evidence

Use for every valid defect.

Required items:

- Summary
- Environment
- Preconditions
- Reproduction steps
- Actual result
- Expected result
- Evidence
- Severity
- Priority
- Impact scope
- Fix verification result

#### [POINT] Regression Evidence

Use before release.

Required items:

- Regression scope
- Regression cases or checklist
- Execution result
- Automation result if available
- Manual evidence for critical flows
- Known regression risk

#### [POINT] Execution Review Evidence

Use after execution and before QA marks the package ready for release
consideration.

Required items:

- Test report
- Defect summary
- Remaining risk list
- Not-tested scope
- Automated/manual execution reconciliation
- QA readiness outcome
- Execution review sign-off

#### [POINT] Post-Release Evidence

Use after release.

Required items:

- Production monitoring result
- Production defect list
- User-impact notes if any
- Escaped defect analysis for important issues
- Improvement actions

---

## [SECTION] Evidence Quality Rules

- Evidence must be understandable by another person later.
- Screenshots should show enough page context, not only a cropped success message.
- Logs should include timestamp and request or error context when possible.
- API evidence should include request, response, status code, and relevant payload.
- API write/update evidence must include a post-write readback of the changed
  record or field, expected value, actual value, and assertion result. A write
  API success response alone is not sufficient evidence that the case passed.
- API write/update tests must verify the test case's core business point. When
  the case describes changing a value, the script must create or confirm a
  different precondition value, execute the target update, and assert that the
  post-write readback changed from the precondition to the target value.
- Dashboard execution history must show human-facing execution outcomes as only
  `Pass` or `Fail`. Raw runner states such as `error`, `undefined`, `untested`,
  `skipped`, or `running` may be retained as technical metadata, but must not be
  shown as the primary execution result in the history timeline.
- Dashboard execution history must be execution-centric: screenshot evidence
  batches, linked bugs, and current workbook snapshots must not render as
  separate history items. Evidence belongs to the matching execution result as
  supporting metadata or artifact paths.
- Database evidence should include query purpose and result summary.
- Test reports should state both tested and not-tested scope.
- Risk notes should be specific enough for a release decision.

---

## [SECTION] Evidence Naming Guidance

Use names that make evidence easy to search:

```text
<project>-<feature>-<case-id>-<result>-<date>
```

Example:

```text
website-login-TC001-pass-2026-05-13
```

---

## [SECTION] Minimum Evidence By Risk Level

#### [POINT] Low Risk

- Checklist or simple test notes
- Execution result
- Screenshot or short evidence note
- Known risk note if any

#### [POINT] Medium Risk

- Test cases
- Execution record
- Defect links
- Screenshot, logs, or API evidence
- Regression notes
- Test summary

#### [POINT] High Risk

- Test strategy
- Reviewed test cases
- Full execution record
- Strong evidence package
- Regression evidence
- Non-functional evidence where relevant
- Test report
- Execution readiness risk review

---

## [SECTION] Not Tested And Partially Tested Areas

Untested or partially tested areas must be documented.

Required fields:

- Area
- Reason
- Risk
- Owner
- Follow-up action
- Target date

---

## [SECTION] Review Rule

If there is no evidence, the status should not be treated as fully tested.
