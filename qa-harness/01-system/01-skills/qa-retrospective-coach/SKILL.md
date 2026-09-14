---
name: qa-retrospective-coach
description: Use this skill to facilitate QA retrospectives for a project, release, sprint, escaped defect, or worker/team quality review. It reviews quality outcomes, process gaps, evidence gaps, metrics, automation value, regression effectiveness, and improvement actions.
---

# QA Retrospective Coach

## Purpose

Guide a structured QA retrospective and turn observations into improvement actions.

The retrospective should improve the QA system, not only summarize what happened.

## Inputs

Use any available input:

- Test report
- Production bug analysis
- Quality metrics
- Defect summary
- Test evidence review
- Automation coverage review
- Team feedback
- Release decision notes

## Reference Documents

When available, align with:

- `../../01-quality-principles.md`
- `../../02-qa-workflow.md`
- `../../06-quality-metrics.md`
- `../../templates/qa-retrospective-template.md`

## Workflow

1. Summarize release or project quality outcome.
2. Review what worked well.
3. Review what did not work well.
4. Connect findings to metrics and evidence.
5. Identify root causes.
6. Propose improvement actions.
7. Identify training needs.
8. Define success criteria and follow-up date.

## Output Format

```markdown
# QA Retrospective

---

## [SECTION] Quality Summary

- Release result:
- Production quality:
- Main risks:
- Main lesson:

---

## [SECTION] What Worked Well

-

---

## [SECTION] What Needs Improvement

| Area | Issue | Impact | Evidence |
|---|---|---|---|
|  |  |  |  |

---

## [SECTION] Root Causes

-

---

## [SECTION] Improvement Actions

| Action | Owner | Due Date | Success Criteria |
|---|---|---|---|
|  |  |  |  |

---

## [SECTION] Training Needs

| Role / Worker | Gap | Training Action | Verification |
|---|---|---|---|
|  |  |  |  |
```

## Quality Rules

- Keep findings evidence-based.
- Avoid vague actions such as "be more careful".
- Every action needs an owner and success criteria.
- Include process, template, skill, automation, and training improvements when relevant.
- Metrics should be interpreted with context.
