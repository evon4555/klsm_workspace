---
name: worker-training-plan
description: Use this skill to create a QA worker training and improvement plan based on test case review findings, execution evidence gaps, production bug analysis, defect report quality, automation gaps, metrics, or retrospective results. It defines observed gaps, training actions, practice tasks, and verification criteria.
---

# Worker Training Plan

## Purpose

Create a focused improvement plan for a QA worker or QA role.

The plan should be specific, evidence-based, and verifiable. It should help the worker improve and then return to project work with measurable progress.

## Inputs

Use any available input:

- Test case review findings
- Evidence checklist result
- Defect report review
- Production bug analysis
- Quality metrics
- Retrospective notes
- Manager or reviewer feedback
- Example work products

## Reference Documents

When available, align with:

- `../../01-quality-principles.md`
- `../../03-qa-roles.md`
- `../../05-evidence-standard.md`
- `../../06-quality-metrics.md`
- `../../templates/worker-training-plan-template.md`

## Workflow

1. Identify observed gaps from evidence.
2. Assess impact on quality.
3. Prioritize skill areas.
4. Define training actions.
5. Define practice tasks.
6. Define verification method and pass criteria.
7. Define follow-up review.

## Output Format

```markdown
# Worker Training Plan

---

## [SECTION] Worker Summary

- Worker:
- Role:
- Main gap:
- Quality impact:

---

## [SECTION] Observed Gaps

| Gap | Evidence | Impact | Priority |
|---|---|---|---|
|  |  |  | High / Medium / Low |

---

## [SECTION] Training Actions

| Action | Purpose | Due Date | Output |
|---|---|---|---|
|  |  |  |  |

---

## [SECTION] Practice Tasks

| Task | Expected Output | Review Criteria |
|---|---|---|
|  |  |  |

---

## [SECTION] Verification Plan

| Verification Item | Method | Pass Criteria | Date |
|---|---|---|---|
|  |  |  |  |

---

## [SECTION] Follow-up

- Follow-up date:
- Expected improvement:
- Remaining risk:
```

## Quality Rules

- Do not create generic training plans.
- Link every gap to evidence or observed behavior.
- Focus on coachable skills and practical work output.
- Verification must include real or realistic QA work.
- Use metrics for improvement, not blame.
