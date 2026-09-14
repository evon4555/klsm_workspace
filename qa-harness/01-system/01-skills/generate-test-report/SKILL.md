---
name: generate-test-report
description: Use this skill to generate a QA execution/readiness test report from test strategy, test cases, execution records, defect list, regression result, evidence links, known risks, and package scope. It summarizes quality status, remaining risks, QA readiness outcome, and required follow-up actions.
---

# Generate Test Report

## Purpose

Generate a clear test report that supports execution review and release
readiness discussion.

The report should explain what was tested, what was not tested, what defects
remain, what evidence exists, and whether QA considers the package ready for
release consideration. QA does not own the final business release decision.

## Inputs

Use any available input:

- Test strategy
- Test execution records
- Test case results
- Defect list
- Regression result
- Automation result
- Performance or security notes
- Evidence links
- Known risks
- Package scope

If input is incomplete, create the report with explicit gaps and mark the conclusion as conditional.

## Reference Documents

When available, align with:

- `../../01-quality-principles.md`
- `../../02-qa-workflow.md`
- `../../04-quality-gates.md`
- `../../05-evidence-standard.md`
- `../../templates/test-report-template.md`
- `../../templates/execution-review-checklist.md`
- `../../templates/test-evidence-checklist.md`

## Workflow

1. Summarize release scope and business impact.
2. Summarize tested and not-tested scope.
3. Summarize execution status.
4. Summarize defects by severity and status.
5. Summarize regression result.
6. Summarize non-functional findings when relevant.
7. Check evidence completeness.
8. List known risks and risk owners.
9. Provide QA readiness outcome.

## Output Format

```markdown
# Test Report

---

## [SECTION] Executive Summary

- Quality conclusion: Pass / Pass With Risk / Not Ready - Fix Required / Blocked / Scope Change Required
- QA readiness outcome: Ready for Release / Ready for Release with Accepted Risk / Not Ready - Fix Required / Blocked / Scope Change Required
- Main reason:

---

## [SECTION] Scope Summary

### [FIELD] Tested Scope

-

### [FIELD] Not Tested Scope

| Area | Reason | Risk | Owner | Follow-up |
|---|---|---|---|---|
|  |  |  |  |  |

---

## [SECTION] Execution Summary

| Metric | Count / Status |
|---|---:|
| Total Cases |  |
| Passed |  |
| Failed |  |
| Blocked |  |
| Skipped |  |
| Pass Rate |  |

---

## [SECTION] Defect Summary

| Severity | Open | Fixed | Accepted | Notes |
|---|---:|---:|---:|---|
| Critical |  |  |  |  |
| High |  |  |  |  |
| Medium |  |  |  |  |
| Low |  |  |  |  |

---

## [SECTION] Regression And Evidence

- Regression result:
- Automation result:
- Evidence completeness:
- Missing evidence:

---

## [SECTION] Known Risks

| Risk | Impact | Mitigation | Owner | Accepted By |
|---|---|---|---|---|
|  |  |  |  |  |

---

## [SECTION] Execution Review Handoff

- QA readiness outcome:
- Required action before release:
- Follow-up after release:
```

## Quality Rules

- Do not hide missing evidence.
- Do not mark a package ready if critical blockers remain unless explicit risk acceptance exists.
- Separate factual test results from recommendation.
- Mark the report conditional when key inputs are missing.
- Known risks must include owner and mitigation or acceptance.
