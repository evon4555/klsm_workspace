---
name: create-regression-plan
description: Use this skill to create a regression test plan from change scope, impacted modules, dependency analysis, defect history, critical business flows, automation coverage, and release risk. It defines what existing functionality should be retested, by which method, with what evidence, and what risk remains.
---

# Create Regression Plan

## Purpose

Create a focused regression plan that protects existing business behavior from being broken by new changes.

The plan should be risk-based. It should not blindly retest everything unless the change risk justifies it.

## Inputs

Use any available input:

- Change summary
- Requirement or release scope
- Code or module impact notes
- Historical defects
- Critical business flows
- Integration points
- Automation coverage
- Test strategy
- Known release risks

If impact information is incomplete, document assumptions and recommend clarification.

## Reference Documents

When available, align with:

- `../../01-quality-principles.md`
- `../../02-qa-workflow.md`
- `../../04-quality-gates.md`
- `../../05-evidence-standard.md`
- `../../templates/regression-plan-template.md`

## Workflow

1. Identify changed areas.
2. Identify directly impacted behavior.
3. Identify indirectly impacted behavior.
4. Review historical defect areas.
5. Select critical business flows for regression.
6. Decide manual, automation, or combined execution.
7. Define evidence requirements.
8. List excluded areas and accepted risks.
9. Define exit criteria and final regression conclusion.

## Regression Scope Rules

Include areas when:

- The module changed directly.
- The module depends on changed behavior.
- The flow is business critical.
- The flow had historical defects.
- The flow shares data, permissions, APIs, or configuration with changed areas.
- Existing automation has weak or missing coverage.

Exclude areas only when the reason and risk are clear.

## Output Format

```markdown
# Regression Plan

---

## [SECTION] Change Impact Summary

- Change summary:
- Changed modules:
- Direct impact:
- Indirect impact:
- Risk level:

---

## [SECTION] Regression Scope

| Area | Reason For Inclusion | Method | Priority | Evidence Required |
|---|---|---|---|---|
|  |  | Manual / Automation / Both | P0 / P1 / P2 / P3 | Yes / No |

---

## [SECTION] Not Included Scope

| Area | Reason For Exclusion | Risk | Accepted By |
|---|---|---|---|
|  |  |  |  |

---

## [SECTION] Regression Cases

| Case ID | Case Name | Priority | Method | Expected Evidence |
|---|---|---|---|---|
|  |  | P0 / P1 / P2 / P3 | Manual / Automation |  |

---

## [SECTION] Automation Usage

- Automation suite:
- Coverage confidence:
- Known flaky cases:
- Manual supplement needed:

---

## [SECTION] Exit Criteria

-

---

## [SECTION] Remaining Risks

| Risk | Impact | Mitigation | Owner |
|---|---|---|---|
|  |  |  |  |
```

## Quality Rules

- Tie every regression area to a change, dependency, defect history, or business-critical flow.
- Do not use automation result blindly; mention coverage confidence and flaky risks.
- If scope is reduced because of timeline or resource limits, document the release risk.
- P0 regression flows should require evidence.
- Regression conclusion must be usable in a test report.
