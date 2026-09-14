---
name: create-test-strategy
description: Use this skill to create a project-level or feature-level QA test strategy from requirements, risk review notes, package/release scope, timeline, QA resources, environments, and constraints. It covers functional, regression, automation, performance, security, compatibility, evidence, entry criteria, exit criteria, and QA readiness recommendation.
---

# Create Test Strategy

## When To Use (Conditional — Project / Subproject Scope)

In the West Kowloon / Antank pipeline, this skill produces **project-level
or subproject-level** strategy, NOT per-requirement-package strategy.
Per-package scope, test types, environment, automation opportunity, and
exit criteria are captured inside the package's
[`consolidate-requirement`](../consolidate-requirement/SKILL.md) doc.

Invoke this skill as a standalone artifact only when:

- **Project kickoff** for a new project under the harness.
- **New subproject** lands (e.g., Website added to a project that
  previously only had Box Office).
- A cross-package release plan needs an explicit strategy artifact for
  stakeholders.

Do not produce a per-requirement-package strategy file — that path
churns; let the consolidation doc carry the per-package strategy
content.

## Purpose

Create a practical test strategy that tells the team what to test, why it matters, how much depth is needed, what evidence is required, and what risks remain.

The strategy should be tool-neutral and business-risk based.

## Inputs

Use any available input:

- Requirement or feature description
- Requirement risk review
- Business priority
- Package / release scope
- Timeline
- QA resources
- Environment and test data constraints
- Known defect history
- Automation availability
- Non-functional requirements

If inputs are incomplete, create a strategy with explicit assumptions and open questions.

## Reference Documents

When available, align with:

- `../../01-quality-principles.md`
- `../../02-qa-workflow.md`
- `../../03-qa-roles.md`
- `../../04-quality-gates.md`
- `../../05-evidence-standard.md`
- `../../templates/test-strategy-template.md`

## Workflow

1. Understand the business goal and affected flows.
2. Define scope and out-of-scope items.
3. Determine risk level.
4. Decide required test types.
5. Assign QA roles or AI worker responsibilities.
6. Define environment and test data needs.
7. Define entry and exit criteria.
8. Define evidence requirements.
9. State release risks and recommendation conditions.

## Strategy Rules

- Match test depth to business risk.
- Include regression when existing behavior may be impacted.
- Include non-functional testing when performance, security, compatibility, reliability, or operations risk exists.
- Do not require heavy process for low-risk work unless business impact justifies it.
- Document untested scope and risk explicitly.

## Output Format

Use this structure:

```markdown
# Test Strategy

---

## [SECTION] Basic Information

- Project:
- Feature / Release:
- Requirement Link:
- Owner:
- Reviewers:
- Risk Level:

---

## [SECTION] Business Context

- Business goal:
- User impact:
- Critical business flows:

---

## [SECTION] Scope

### [FIELD] In Scope

-

### [FIELD] Out Of Scope

-

### [FIELD] Assumptions

-

---

## [SECTION] Risk Analysis

| Risk Area | Risk | Impact | Mitigation |
|---|---|---|---|
|  |  |  |  |

---

## [SECTION] Test Types

| Test Type | Required | Scope | Owner | Evidence |
|---|---|---|---|---|
| Functional | Yes / No |  |  |  |
| Regression | Yes / No |  |  |  |
| Automation | Yes / No |  |  |  |
| Performance | Yes / No |  |  |  |
| Security | Yes / No |  |  |  |
| Compatibility | Yes / No |  |  |  |

---

## [SECTION] Entry Criteria

-

---

## [SECTION] Exit Criteria

-

---

## [SECTION] Evidence Requirements

-

---

## [SECTION] QA Readiness Recommendation Conditions

- Proceed if:
- Proceed with risk if:
- Do not proceed if:
```

## Quality Rules

- A strategy must be actionable, not theoretical.
- Every required test type needs a reason.
- Every excluded test type should have a rationale if risk is medium or high.
- Known risks must be visible to release decision makers.
- Prefer clear tables and checklists over long prose.
