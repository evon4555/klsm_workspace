---
name: create-automation-plan
description: Use this skill to identify which functional, regression, API, UI, integration, or E2E test cases should be automated. It prioritizes automation candidates by business value, stability, execution frequency, maintenance cost, and regression risk, and outputs a tool-neutral automation strategy.
---

# Create Automation Plan

## Purpose

Create an automation plan that reduces repeated manual effort and protects important business flows.

Automation should be selected by value and maintainability, not by case count.

## Inputs

Use any available input:

- Test strategy
- Test cases
- Regression plan
- Critical business flows
- Defect history
- Manual execution effort
- Existing automation coverage
- Environment and data constraints
- CI/CD constraints

## Reference Documents

When available, align with:

- `../../01-quality-principles.md`
- `../../02-qa-workflow.md`
- `../../05-evidence-standard.md`
- `../../templates/automation-strategy-template.md`

## Workflow

1. Identify repeated manual testing effort.
2. Identify business-critical flows.
3. Identify stable and high-value automation candidates.
4. Choose the right test layer: API, UI, integration, or E2E.
5. Exclude poor automation candidates with reasons.
6. Define execution trigger and evidence.
7. Define maintenance risks and success metrics.

## Candidate Selection Rules

Good candidates usually have:

- High business value
- Frequent regression need
- Stable behavior
- Clear expected result
- Reliable test data
- Low to reasonable maintenance cost

Poor candidates usually have:

- Frequently changing UI or logic
- Unclear expected result
- Heavy manual judgment
- Unstable environment
- Difficult data setup without clear value

## Output Format

```markdown
# Automation Plan

---

## [SECTION] Automation Goal

- Business goal:
- Manual effort to reduce:
- Critical flows to protect:

---

## [SECTION] Candidate Review

| Case / Flow | Business Priority | Stability | Frequency | Recommended Layer | Decision | Reason |
|---|---|---|---|---|---|---|
|  | P0 / P1 / P2 / P3 | Stable / Changing / Unclear | High / Medium / Low | API / UI / Integration / E2E | Automate / Manual / Later |  |

---

## [SECTION] Execution Strategy

- Trigger:
- Environment:
- Data strategy:
- Report:
- Failure notification:

---

## [SECTION] Maintenance Risks

| Risk | Impact | Mitigation |
|---|---|---|
|  |  |  |

---

## [SECTION] Final Recommendation

- Start now:
- Do later:
- Keep manual:
```

## Quality Rules

- Prefer API or service-level automation when it gives reliable coverage with lower maintenance.
- Use UI or E2E automation for critical user journeys, not every UI detail.
- Every automation candidate must have a clear reason.
- Mention data and environment risks explicitly.
- Do not treat unstable automation as quality evidence without caveats.
