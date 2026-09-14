# AI QA System Todo List


---

## [SECTION] Goal

Build an AI-assisted QA system that makes software testing more business-aligned, process-driven, evidence-based, and continuously improvable.

The first version should stay practical: define the quality rules, create the core workflow documents, then introduce AI skills step by step.

---

## [SECTION] Phase 1: Foundation

- [x] Create `README.md` as the entry point for the AI QA system.
- [x] Create `01-quality-principles.md` to define the testing and quality engineering philosophy.
- [x] Create `02-qa-workflow.md` to describe the end-to-end QA workflow.
- [x] Create `03-qa-roles.md` to define QA roles such as functional QA, automation QA, performance QA, security QA, and quality reviewer.
- [x] Create `04-quality-gates.md` to define stage gates before development completion, test execution, release, and post-release closure.
- [x] Create `05-evidence-standard.md` to define what evidence is required before a task can be considered tested.

---

## [SECTION] Phase 2: Core Templates

- [x] Create `templates/test-strategy-template.md` for project-level test strategy.
- [x] Create `templates/test-case-template.md` for functional test cases.
- [x] Create `templates/test-case-review-template.md` for test case review.
- [x] Create `templates/test-execution-record-template.md` for execution evidence.
- [x] Create `templates/test-report-template.md` for release test reports.
- [x] Create `templates/bug-report-template.md` for defect reporting.
- [x] Create `templates/regression-plan-template.md` for regression scope and execution planning.

---

## [SECTION] Phase 3: First AI Skills

- [x] Create `skills/review-requirement-risk/SKILL.md` to review requirement ambiguity, business risk, dependency risk, data risk, permission risk, and edge cases.
- [x] Create `skills/create-test-strategy/SKILL.md` to generate a test strategy from requirements, scope, timeline, risks, and available QA resources.
- [x] Create `skills/write-test-case/SKILL.md` to generate structured test cases with positive, negative, boundary, permission, data, and regression coverage.
- [x] Create `skills/review-test-case/SKILL.md` to review test cases for coverage, executability, traceability, clarity, and missing risk areas.

---

## [SECTION] Phase 4: Delivery And Evidence

- [x] Create `skills/generate-test-report/SKILL.md` to produce release-ready test reports from execution records, defects, risks, and coverage.
- [x] Create `skills/create-regression-plan/SKILL.md` to generate regression plans from change scope, impacted modules, historical defects, and release risk.
- [x] Create `templates/execution-review-checklist.md` to standardize QA readiness review; keep `release-quality-checklist.md` only as a compatibility alias.
- [x] Create `templates/test-evidence-checklist.md` to ensure screenshots, logs, links, reports, and risk notes are captured.

---

## [SECTION] Phase 5: Automation And Non-Functional Testing

- [x] Create `templates/automation-strategy-template.md` to define what should be automated and why.
- [x] Create `skills/create-automation-plan/SKILL.md` to identify automation candidates and prioritize them.
- [x] Create `skills/review-automation-coverage/SKILL.md` to evaluate whether automation coverage protects important business flows.
- [x] Create `templates/performance-test-plan-template.md` for performance scope, workload model, metrics, environment, and acceptance criteria.
- [x] Create `skills/create-performance-test-plan/SKILL.md` for performance testing plans.
- [x] Create `templates/security-test-checklist.md` for authentication, authorization, input validation, sensitive data, and audit checks.
- [x] Create `skills/create-security-checklist/SKILL.md` for security test planning.

---

## [SECTION] Phase 6: Quality Metrics And Improvement

- [x] Create `06-quality-metrics.md` to define project, process, automation, and worker-level metrics.
- [x] Create `templates/production-bug-analysis-template.md` for online bug review.
- [x] Create `skills/analyze-production-bug/SKILL.md` to identify escaped-defect causes and improvement actions.
- [x] Create `templates/qa-retrospective-template.md` for project and worker retrospectives.
- [x] Create `skills/qa-retrospective-coach/SKILL.md` to generate retrospective findings and improvement plans.
- [x] Create `templates/worker-training-plan-template.md` for training and verification plans.
- [x] Create `skills/worker-training-plan/SKILL.md` to generate improvement plans for QA workers based on review findings and metrics.

---

## [SECTION] Phase 7: Trial Run

- [x] Select one real requirement or feature from the Website project: `D:\Workspace\west-kowloon\01-requirements\02-subprojects\02-website\02-modules\01-login-registration\2026-06-16`.
- [x] Run `review-requirement-risk` against the requirement.
- [x] Run `create-test-strategy` for the selected feature.
- [x] Run `write-test-case` to generate test cases.
- [x] Run `review-test-case` to improve the generated test cases.
- [x] **(Added 2026-05-15)** Capture mindmap registration/login sub-tree and cross-check against PRDs; revise risk review and test cases in place; resolve source-authority for the project.
- [x] **(Added 2026-05-15)** Sediment learnings into the QA system: new `07-source-authority.md`; updates to `project-context.md`, `02-qa-workflow.md`, `review-requirement-risk` SKILL, `write-test-case` SKILL, `test-case-template.md`.
- [ ] Execute the test cases manually and collect evidence.
- [ ] Generate a test report.
- [ ] Record problems found in the workflow and update the templates or skills.

---

## [SECTION] Working Rules

- AI generates plans, drafts, reviews, and suggestions.
- Humans make final quality decisions, risk tradeoffs, and release approvals.
- Every tested item should have traceable evidence.
- Every escaped defect should improve the system.
- Metrics should drive improvement, not blame.
- Start small, run on real work, then improve the system based on evidence.
