---
name: analyze-production-bug
description: Use this skill to analyze an escaped production bug or incident from a QA and quality engineering perspective. It identifies why the issue escaped, whether requirement review, test strategy, test cases, execution, regression, automation, monitoring, or release gates failed, and recommends system improvement actions.
---

# Analyze Production Bug

## Purpose

Analyze a production bug as feedback to the QA system.

The goal is not blame. The goal is to find which part of the system failed and how to reduce repeat risk.

## Inputs

Use any available input:

- Production bug report
- Incident timeline
- Test report
- Test cases
- Execution evidence
- Regression plan
- Automation result
- Requirement or design notes
- Logs, screenshots, monitoring, or user reports

## Reference Documents

When available, align with:

- `../../01-quality-principles.md`
- `../../02-qa-workflow.md`
- `../../04-quality-gates.md`
- `../../05-evidence-standard.md`
- `../../06-quality-metrics.md`
- `../../templates/production-bug-analysis-template.md`

## Workflow

1. Summarize the bug and business impact.
2. Reconstruct the timeline.
3. Identify the direct cause if known.
4. Analyze why it escaped testing.
5. Map the escape reason to process, template, skill, automation, monitoring, or training gaps.
6. Recommend concrete improvement actions.
7. Define verification for those actions.

## Output Format

```markdown
# Production Bug Analysis

---

## [SECTION] Problem Summary

- Bug:
- Business impact:
- Affected scope:
- Severity:

---

## [SECTION] Escape Analysis

| Area | Finding | Evidence | Improvement Needed |
|---|---|---|---|
| Requirement |  |  |  |
| Test design |  |  |  |
| Execution |  |  |  |
| Regression |  |  |  |
| Automation |  |  |  |
| Monitoring |  |  |  |
| Release gate |  |  |  |

---

## [SECTION] Root Cause

-

---

## [SECTION] Improvement Actions

| Action | Type | Owner | Due Date | Verification |
|---|---|---|---|---|
|  | Process / Template / Skill / Automation / Training / Monitoring |  |  |  |

---

## [SECTION] Final Conclusion

- Main escape reason:
- System update required:
- Follow-up review date:
```

## Quality Rules

- Separate direct technical cause from QA escape cause.
- Do not stop at "tester missed it"; identify why the system allowed the miss.
- Every important finding should lead to an action.
- Actions must be verifiable.
- If evidence is missing, mark the analysis as limited.
