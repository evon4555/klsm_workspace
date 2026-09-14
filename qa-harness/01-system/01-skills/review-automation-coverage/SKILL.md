---
name: review-automation-coverage
description: Use this skill to review existing or proposed automation coverage for business value, critical flow protection, regression usefulness, stability, flaky risk, test layer balance, maintainability, and missing coverage. It checks whether automation coverage is meaningful rather than only high in case count.
---

# Review Automation Coverage

## Purpose

Evaluate whether automation protects important business flows and provides reliable release feedback.

The review should identify false confidence, missing critical coverage, unstable tests, and overinvestment in low-value automation.

## Inputs

Use any available input:

- Automation plan
- Automated test list
- Test execution reports
- Flaky test records
- Manual regression scope
- Critical business flows
- Defect history
- Release quality goals

## Reference Documents

When available, align with:

- `../../01-quality-principles.md`
- `../../05-evidence-standard.md`
- `../../templates/automation-strategy-template.md`

## Workflow

1. Identify what business flows automation claims to cover.
2. Compare automation coverage against critical flows and regression risks.
3. Review test layer balance.
4. Review stability and flaky risk.
5. Review maintainability and data dependency.
6. Identify missing or weak coverage.
7. Provide improvement recommendations.

## Output Format

```markdown
# Automation Coverage Review

---

## [SECTION] Coverage Summary

- Overall result: Strong / Partial / Weak / Unclear
- Main strength:
- Main risk:

---

## [SECTION] Business Flow Coverage

| Business Flow | Importance | Automation Coverage | Confidence | Gap |
|---|---|---|---|---|
|  | P0 / P1 / P2 / P3 | Covered / Partial / Missing | High / Medium / Low |  |

---

## [SECTION] Stability Review

| Suite / Case | Stability | Risk | Action |
|---|---|---|---|
|  | Stable / Flaky / Unknown |  |  |

---

## [SECTION] Layer Review

| Layer | Coverage | Concern | Recommendation |
|---|---|---|---|
| API |  |  |  |
| UI |  |  |  |
| Integration |  |  |  |
| E2E |  |  |  |

---

## [SECTION] Findings

| Severity | Finding | Impact | Recommendation |
|---|---|---|---|
| Critical / Major / Minor |  |  |  |

---

## [SECTION] Final Recommendation

- Keep:
- Improve:
- Add:
- Remove or de-prioritize:
```

## Quality Rules

- Do not equate case count with coverage quality.
- Critical business flow coverage is more important than broad low-value coverage.
- Flaky tests should be called out as release signal risk.
- Automation that requires heavy manual interpretation should not be treated as strong evidence.
- Recommend manual supplement where automation is weak.
