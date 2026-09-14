---
name: create-performance-test-plan
description: Use this skill to create a performance test plan for APIs, user flows, batch jobs, integrations, or releases. It defines performance objectives, workload model, metrics, acceptance criteria, environment, test data, monitoring, risks, and QA readiness recommendation.
---

# Create Performance Test Plan

## Purpose

Create a practical performance test plan based on business risk and expected usage.

The plan should clarify what performance risk matters, what workload should be simulated, what metrics will be judged, and what result is acceptable.

## Inputs

Use any available input:

- Requirement
- Architecture or API notes
- Production traffic expectations
- User volume
- Data volume
- SLA or acceptance criteria
- Historical performance issues
- Environment constraints
- Monitoring availability

## Reference Documents

When available, align with:

- `../../01-quality-principles.md`
- `../../02-qa-workflow.md`
- `../../04-quality-gates.md`
- `../../templates/performance-test-plan-template.md`

## Workflow

1. Identify why performance matters for the business.
2. Identify target scenarios.
3. Define workload model.
4. Define metrics and acceptance criteria.
5. Define test data and environment.
6. Define monitoring and evidence.
7. Identify risks and limitations.
8. Provide pass criteria and QA readiness recommendation rules.

## Output Format

```markdown
# Performance Test Plan

---

## [SECTION] Objective

- Business goal:
- Performance risk:
- Target users / systems:

---

## [SECTION] Scope

- In scope:
- Out of scope:

---

## [SECTION] Workload Model

| Scenario | Volume | Duration | Ramp-up | Data Volume | Purpose |
|---|---:|---|---|---:|---|
| Baseline |  |  |  |  |  |
| Peak |  |  |  |  |  |
| Stress |  |  |  |  |  |

---

## [SECTION] Metrics And Criteria

| Metric | Target | Threshold | Evidence |
|---|---:|---:|---|
| Response time P95 |  |  |  |
| Throughput |  |  |  |
| Error rate |  |  |  |
| CPU / Memory |  |  |  |

---

## [SECTION] Environment And Data

- Environment:
- Test data:
- Monitoring:
- Known limitations:

---

## [SECTION] Risks And Recommendation

- Risks:
- Pass criteria:
- QA readiness recommendation rule:
```

## Quality Rules

- Avoid vague goals such as "system should be fast".
- Tie metrics to business or user impact.
- State environment limitations clearly.
- Include error rate, not only response time.
- If realistic production volume is unknown, provide assumptions and questions.
