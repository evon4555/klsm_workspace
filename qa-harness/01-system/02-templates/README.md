# 01-system/02-templates/

Drop-in templates that get filled to produce concrete project deliverables.
Most are designed to be the *output* shape of one of the AI skills in
[`../01-skills/`](../01-skills/README.md).

## Templates

### Test design + execution
- [`test-strategy-template.md`](./test-strategy-template.md) — project-level test strategy.
- [`requirement-consolidation-template.md`](./requirement-consolidation-template.md) — gate doc between requirement analysis and test case design; Test Manager sign-off required before `03-test-design/` is written.
- [`test-case-template.md`](./test-case-template.md) — single test case (precursor to xlsx).
- [`test-case-review-template.md`](./test-case-review-template.md) — QA2 AI review checklist. Human/Test Manager sign-off lives in `04-test-case-review/` as paired `.md + .docx`.
- [`test-execution-record-template.md`](./test-execution-record-template.md) — per-execution evidence.
- [`test-evidence-checklist.md`](./test-evidence-checklist.md) — what must be captured.
- [`regression-plan-template.md`](./regression-plan-template.md) — regression scope.

### Reporting + readiness
- [`test-report-template.md`](./test-report-template.md) — execution summary and QA readiness report.
- [`execution-review-checklist.md`](./execution-review-checklist.md) — `06-execution-review` readiness sign-off.
- [`release-quality-checklist.md`](./release-quality-checklist.md) — compatibility alias for old links; use `execution-review-checklist.md` for new packages.
- [`bug-report-template.md`](./bug-report-template.md) — defect reporting.

### Non-functional + special
- [`automation-strategy-template.md`](./automation-strategy-template.md) — what to automate and why.
- [`performance-test-plan-template.md`](./performance-test-plan-template.md) — perf workload + metrics.
- [`security-test-checklist.md`](./security-test-checklist.md) — security test plan.

### Continuous improvement
- [`release-feedback-template.md`](./release-feedback-template.md) — `07-release-feedback` feedback loop.
- [`production-bug-analysis-template.md`](./production-bug-analysis-template.md) — escape analysis.
- [`qa-retrospective-template.md`](./qa-retrospective-template.md) — retrospective.
- [`worker-training-plan-template.md`](./worker-training-plan-template.md) — improvement plan.

## See also

- [`../01-skills/`](../01-skills/README.md) — AI skills that produce these
- [`../README.md`](../README.md) — 01-system overview
- `D:\Workspace\west-kowloon\01-requirements` — where West Kowloon filled-in artifacts land
