# AI QA System


---

## [SECTION] Purpose

AI QA System is a shared quality engineering framework for all projects under Kasi.

Its purpose is to make testing more business-aligned, process-driven, evidence-based, and continuously improvable. AI should help QA teams draft plans, identify risks, generate test cases, review coverage, summarize evidence, and analyze quality problems. Human reviewers remain responsible for final decisions, tradeoffs, and release approval.

---

## [SECTION] Core Idea

Business value depends on product quality. Testing exists to protect business quality, not just to execute cases or find bugs.

Quality assurance should become part of the delivery flow. It should not depend only on individual memory, personal habits, or different QA experience levels. A stable QA system needs shared standards, repeatable workflows, required evidence, clear quality gates, and continuous improvement based on real defects and metrics.

---

## [SECTION] Operating Model

The system follows this model:

- AI proposes plans, test cases, reviews, reports, and improvement suggestions.
- QA reviews AI output, adjusts it for business context, and owns the final testing conclusion.
- Project teams follow the same quality gates before moving to the next delivery stage.
- Testing evidence is required for traceability and future improvement.
- Production issues are used to improve requirements review, test design, automation, monitoring, and training.

---

## [SECTION] Foundation Documents

- [`01-quality-principles.md`](./01-quality-principles.md): Quality philosophy and decision principles.
- [`02-qa-workflow.md`](./02-qa-workflow.md): End-to-end QA workflow from requirement review to post-release improvement.
- [`03-qa-roles.md`](./03-qa-roles.md): QA role model for functional, automation, performance, security, and quality review work.
- [`04-quality-gates.md`](./04-quality-gates.md): Required gates before test execution, release, and closure.
- [`05-evidence-standard.md`](./05-evidence-standard.md): Evidence rules that define what "tested" means.
- [`06-quality-metrics.md`](./06-quality-metrics.md): Project, process, automation, and worker-level metrics.
- [`07-source-authority.md`](./07-source-authority.md): How to treat conflicting / silent / hierarchical input sources (PRD, mindmap, Figma, functional spec). Project-specific authority declarations.
- [`08-our-pipeline.md`](./08-our-pipeline.md): **Our concrete pipeline** (West Kowloon / Antank) — instance of 02-qa-workflow with role attribution, tooling (Behave + Playwright + requests), dashboard, and future ZenTao integration.
- [`10-change-management.md`](./10-change-management.md): How requirement changes are versioned, soft-deleted, and tracked. ISO-date versioning, mandatory `CHANGE.md`, RAG-style maintenance scan when xlsx updates.
- [`11-rule-promotion.md`](./11-rule-promotion.md): **Project ↔ system sync** — how rules surfaced in one project get promoted to `01-system` (or kept project-permanent). Triggered by `01-system/03-tools/check_rule_drift.py`.
- [`12-md-docx-handoff.md`](./12-md-docx-handoff.md): **MD / DOCX hand-off** — convention for AI-drafted review artifacts (consolidation, test case review, test report): `.md` is canonical, `.docx` is the human review derivative, reviewers edit `.docx`, AI absorbs edits back via `01-system/03-tools/md_docx.py`.

---

## [SECTION] Templates ([`02-templates/`](./02-templates/))

Drop-in templates that turn into project deliverables. Filled by QA + AI together.

- [`test-strategy-template.md`](./02-templates/test-strategy-template.md) — project-level test strategy.
- [`requirement-consolidation-template.md`](./02-templates/requirement-consolidation-template.md) — requirement review / scope sign-off gate before test design.
- [`test-case-template.md`](./02-templates/test-case-template.md) — single test case (used to draft cases that later get rolled into xlsx).
- [`test-case-review-template.md`](./02-templates/test-case-review-template.md) — QA2 AI review checklist; final human sign-off uses `04-test-case-review/` with paired `.md + .docx`.
- [`test-execution-record-template.md`](./02-templates/test-execution-record-template.md) — per-execution evidence.
- [`test-report-template.md`](./02-templates/test-report-template.md) — execution summary and QA readiness report.
- [`test-evidence-checklist.md`](./02-templates/test-evidence-checklist.md) — what must be captured.
- [`regression-plan-template.md`](./02-templates/regression-plan-template.md) — regression scope + execution plan.
- [`automation-strategy-template.md`](./02-templates/automation-strategy-template.md) — what to automate and why.
- [`performance-test-plan-template.md`](./02-templates/performance-test-plan-template.md) — perf scope, workload, metrics, acceptance.
- [`security-test-checklist.md`](./02-templates/security-test-checklist.md) — authn / authz / input validation / sensitive data / audit.
- [`execution-review-checklist.md`](./02-templates/execution-review-checklist.md) — `06-execution-review` readiness sign-off.
- [`release-feedback-template.md`](./02-templates/release-feedback-template.md) — `07-release-feedback` feedback loop.
- [`release-quality-checklist.md`](./02-templates/release-quality-checklist.md) — compatibility alias for old links.
- [`bug-report-template.md`](./02-templates/bug-report-template.md) — defect reporting.
- [`production-bug-analysis-template.md`](./02-templates/production-bug-analysis-template.md) — escape analysis.
- [`qa-retrospective-template.md`](./02-templates/qa-retrospective-template.md) — team retrospective.
- [`worker-training-plan-template.md`](./02-templates/worker-training-plan-template.md) — per-worker improvement plan.

---

## [SECTION] AI Skills ([`01-skills/`](./01-skills/))

Reusable AI prompts. Each is a directory with a `SKILL.md` describing the
input/output contract.

- Risk + strategy: [`review-requirement-risk`](./01-skills/review-requirement-risk/SKILL.md), [`create-test-strategy`](./01-skills/create-test-strategy/SKILL.md)
- Test case work: [`write-test-case`](./01-skills/write-test-case/SKILL.md), [`review-test-case`](./01-skills/review-test-case/SKILL.md)
- Automation + perf + security: [`create-automation-plan`](./01-skills/create-automation-plan/SKILL.md), [`review-automation-coverage`](./01-skills/review-automation-coverage/SKILL.md), [`create-performance-test-plan`](./01-skills/create-performance-test-plan/SKILL.md), [`create-security-checklist`](./01-skills/create-security-checklist/SKILL.md)
- Regression + reporting: [`create-regression-plan`](./01-skills/create-regression-plan/SKILL.md), [`generate-test-report`](./01-skills/generate-test-report/SKILL.md)
- Post-release + improvement: [`analyze-production-bug`](./01-skills/analyze-production-bug/SKILL.md), [`qa-retrospective-coach`](./01-skills/qa-retrospective-coach/SKILL.md), [`worker-training-plan`](./01-skills/worker-training-plan/SKILL.md)

---

## [SECTION] Validators ([`03-tools/`](./03-tools/README.md))

The harness contract layer — PASS/FAIL scripts that enforce consistency
between xlsx requirements, .feature automation, and dashboard.db results.
See [`03-tools/README.md`](./03-tools/README.md) for the full list. Main entry:

```powershell
python .\01-system\03-tools\gate.py
```

`gate.py` chains 6 validators including `check_signoff_gate.py` (Step 3.5
sign-off respected, no test cases for unsigned consolidations) and
`check_testcase_review_gate.py` (test-case review signed, dated, and free of
open comments before execution readiness).

---

## [SECTION] Runtime view: Package Health dashboard

The Package Health page on the dashboard (`02-platform/02-dashboard`)
gives a live filesystem-driven view of every requirement package against
this workflow. Each row is one date package; each column is one workflow
stage (01-input … 07-release-feedback) with a status badge derived from real
artifacts on disk.

What the dashboard surfaces beyond the offline `gate.py`:

- per-package drill-down with file lists per stage
- click any file → opens in WPS / Word / Notepad (OS default)
- "Generate review .docx" button → wraps `03-tools/md_docx.py to-docx`
  (see [`12-md-docx-handoff.md`](./12-md-docx-handoff.md))
- "Run xlsx validator" button → wraps `validate_testcase_xlsx.py`
- "Show linked runs" button → joins package case-IDs to `dashboard.db`
  test runs

Backed by `01-system/03-tools/package_scanner.py`.

The dashboard also has a separate **Quality System** page (governance /
build-flow spec) which defines the meta-rules the harness is built
against. The two pages are deliberately separate — see the dashboard
README for the distinction.

---

## [SECTION] Target Workflow

1. Review requirement risks.
2. Create a test strategy.
3. Design and review test cases.
4. Execute tests and collect evidence.
5. Track defects and verify fixes.
6. Run regression testing.
7. Generate a test report.
8. Review execution readiness.
9. Capture release feedback and analyze production issues.
10. Improve the QA system based on evidence and metrics.

---

## [SECTION] Governance Rules

- No requirement should enter testing without risk review.
- No test execution should start without a test strategy for non-trivial work.
- No feature should be marked as tested without evidence.
- No package should be marked ready for release consideration without a clear
  QA readiness conclusion and known risk list.
- No escaped defect should be closed without analysis and improvement action.
- Metrics should drive improvement, not blame.

---

## [SECTION] How To Use This System

Start from the Phase 1 documents to align on standards. Then create templates and AI skills step by step. Each project can adopt the same framework while keeping project-specific test plans, reports, evidence, and metrics in its own project directory.

For Kasi project work, combine this QA system with the knowledge-base layers:

1. Requirement package
2. Project context
3. Company context
4. AI QA system standards

Requirement-specific facts should drive the actual QA output. Project and company context are supporting background.
